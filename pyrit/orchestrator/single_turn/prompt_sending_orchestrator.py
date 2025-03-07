# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging
import uuid
from typing import Optional, Union

from colorama import Fore, Style

from pyrit.common.display_response import display_image_response
from pyrit.common.utils import combine_dict
from pyrit.models import PromptDataType, PromptRequestResponse
from pyrit.models.filter_criteria import PromptConverterState, PromptFilterCriteria
from pyrit.orchestrator import Orchestrator
from pyrit.prompt_converter import PromptConverter
from pyrit.prompt_normalizer import NormalizerRequest, PromptNormalizer
from pyrit.prompt_target import PromptChatTarget, PromptTarget
from pyrit.score import Scorer

logger = logging.getLogger(__name__)


class PromptSendingOrchestrator(Orchestrator):
    """
    This orchestrator takes a set of prompts, converts them using the list of PromptConverters,
    sends them to a target, and scores the resonses with scorers (if provided).
    """

    def __init__(
        self,
        objective_target: PromptTarget,
        prompt_converters: Optional[list[PromptConverter]] = None,
        scorers: Optional[list[Scorer]] = None,
        batch_size: int = 1,
        verbose: bool = False,
    ) -> None:
        """
        Args:
            objective_target (PromptTarget): The target for sending prompts.
            prompt_converters (list[PromptConverter], Optional): List of prompt converters. These are stacked in
                the order they are provided. E.g. the output of converter1 is the input of converter2.
            scorers (list[Scorer], Optional): List of scorers to use for each prompt request response, to be
                scored immediately after receiving response. Default is None.
            batch_size (int, Optional): The (max) batch size for sending prompts. Defaults to 10.
                Note: If providing max requests per minute on the prompt_target, this should be set to 1 to
                ensure proper rate limit management.
        """
        super().__init__(prompt_converters=prompt_converters, verbose=verbose)

        self._prompt_normalizer = PromptNormalizer()
        self._scorers = scorers or []

        self._objective_target = objective_target

        self._batch_size = batch_size
        self._prepended_conversation: list[PromptRequestResponse] = None

    def set_prepended_conversation(self, *, prepended_conversation: list[PromptRequestResponse]):
        """
        Prepends a conversation to the prompt target.

        This is sent along with each prompt request and can be the first part of aa conversation.
        """
        if prepended_conversation and not isinstance(self._objective_target, PromptChatTarget):
            raise TypeError(
                f"Only PromptChatTargets are able to modify conversation history. Instead objective_target is: "
                f"{type(self._objective_target)}."
            )

        self._prepended_conversation = prepended_conversation

    async def get_prepended_conversation_async(
        self, *, normalizer_request: NormalizerRequest
    ) -> Optional[list[PromptRequestResponse]]:
        """
        Returns the prepended conversation for the normalizer request.

        Can be overwritten by subclasses to provide a different conversation.
        """
        if self._prepended_conversation:
            return self._prepended_conversation

        return None

    def set_skip_criteria(
        self, *, skip_criteria: PromptFilterCriteria, skip_value_type: PromptConverterState = "original"
    ):
        """
        Sets the skip criteria for the orchestrator.

        If prompts match this in memory, then they won't be sent to a target.
        """
        self._prompt_normalizer.set_skip_criteria(skip_criteria=skip_criteria, skip_value_type=skip_value_type)

    async def send_normalizer_requests_async(
        self,
        *,
        prompt_request_list: list[NormalizerRequest],
        memory_labels: Optional[dict[str, str]] = None,
    ) -> list[PromptRequestResponse]:
        """
        Sends the normalized prompts to the prompt target.
        """

        expected_output_list = []
        request_prompts = []
        self.validate_normalizer_requests(prompt_request_list=prompt_request_list)

        for prompt in prompt_request_list:
            prompt.conversation_id = await self._prepare_conversation_async(normalizer_request=prompt)
            request_prompts.append(prompt.seed_prompt_group.prompts[0].value)
            if prompt.seed_prompt_group.prompts[0].expected_output:
                expected_output_list.append(prompt.seed_prompt_group.prompts[0].expected_output)

        # Normalizer is responsible for storing the requests in memory
        # The labels parameter may allow me to stash class information for each kind of prompt.
        responses: list[PromptRequestResponse] = await self._prompt_normalizer.send_prompt_batch_to_target_async(
            requests=prompt_request_list,
            target=self._objective_target,
            labels=combine_dict(existing_dict=self._global_memory_labels, new_dict=memory_labels),
            orchestrator_identifier=self.get_identifier(),
            batch_size=self._batch_size,
        )

        response_pieces = []
        if self._scorers and responses:
            response_pieces = PromptRequestResponse.flatten_to_prompt_request_pieces(responses)

            # ToDo: Only perform this when relevancy or similarity evaluation is needed
            # The responses object is a list of PromptRequestResponse objects from the target
            # Which is sent as a request to scorer
            # Expected Output and Reference Prompt are used as variables in scorer's system prompt for evaluation
            for i, piece in enumerate(response_pieces):
                if i < len(expected_output_list):
                    piece.expected_output = expected_output_list[i]
                if i < len(request_prompts):
                    piece.prompt_metadata["reference_prompt"] = request_prompts[i]

        for scorer in self._scorers:
                await scorer.score_responses_inferring_tasks_batch_async(
                    request_responses=response_pieces, batch_size=10
                )

        return responses

    async def send_prompts_async(
        self,
        *,
        prompt_list: list[str],
        expected_output_list: list[str] = None,
        prompt_type: PromptDataType = "text",
        memory_labels: Optional[dict[str, str]] = None,
        metadata: Optional[dict[str, Union[str, int]]] = None,
    ) -> list[PromptRequestResponse]:
        """
        Sends the prompts to the prompt target.

        Args:
            prompt_list (list[str]): The list of prompts to be sent.
            prompt_type (PromptDataType): The type of prompt data. Defaults to "text".
            memory_labels (dict[str, str], Optional): A free-form dictionary of additional labels to apply to the
                prompts. Any labels passed in will be combined with self._global_memory_labels (from the
                GLOBAL_MEMORY_LABELS environment variable) into one dictionary. In the case of collisions,
                the passed-in labels take precedence. Defaults to None.
            metadata (Optional(dict[str, str | int]): Any additional information to be added to the memory entry
                corresponding to the prompts sent.

        Returns:
            list[PromptRequestResponse]: The responses from sending the prompts.
        """

        if isinstance(prompt_list, str):
            prompt_list = [prompt_list]

        requests: list[NormalizerRequest] = []

        i= 0
        for prompt in prompt_list:
            requests.append(
                self._create_normalizer_request(
                    prompt_text=prompt,
                    expected_output=expected_output_list[i] if expected_output_list else None,
                    prompt_type=prompt_type,
                    converters=self._prompt_converters,
                    metadata=metadata,
                    conversation_id=str(uuid.uuid4()),
                )
            )
            i+=1

        return await self.send_normalizer_requests_async(
            prompt_request_list=requests,
            memory_labels=memory_labels,
        )

    async def print_conversations_async(self):
        """Prints the conversation between the objective target and the red teaming bot."""
        messages = self.get_memory()

        last_conversation_id = None

        for message in messages:
            if message.conversation_id != last_conversation_id:
                print(f"{Style.NORMAL}{Fore.RESET}Conversation ID: {message.conversation_id}")
                last_conversation_id = message.conversation_id

            if message.role == "user" or message.role == "system":
                print(f"\n{Style.BRIGHT}{Fore.LIGHTBLACK_EX}{message.role.capitalize()}: {Style.NORMAL}{message.converted_value}")
            else:
                print(f"{Style.BRIGHT}{Fore.LIGHTBLACK_EX}{message.role.capitalize()}: {Style.NORMAL}{message.converted_value}")
                await display_image_response(message)

            for score in message.scores:
                if float(score.score_value) > 0.7:
                    print(f"{Style.BRIGHT}{Fore.LIGHTGREEN_EX}Score: {Fore.LIGHTGREEN_EX}{score.score_value} : {Style.NORMAL}{score.score_rationale}")
                else:
                    print(f"{Style.BRIGHT}{Fore.LIGHTRED_EX}Score: {Fore.LIGHTRED_EX}{score.score_value} : {Style.NORMAL}{score.score_rationale}")

    def validate_normalizer_requests(self, *, prompt_request_list: list[NormalizerRequest]):
        """
        Validates the normalizer request.

        This is a no-op for this orchestrator, but subclasses may want to implement this.
        """
        pass

    async def _prepare_conversation_async(self, normalizer_request: NormalizerRequest) -> str:
        """
        Adds the conversation to memory if there is a prepended conversation, and return the conversation ID.
        """
        conversation_id = str(uuid.uuid4())

        prepended_conversation = await self.get_prepended_conversation_async(normalizer_request=normalizer_request)
        if prepended_conversation:
            for request in prepended_conversation:
                for piece in request.request_pieces:
                    piece.conversation_id = conversation_id
                    piece.orchestrator_identifier = self.get_identifier()

                    # if the piece is retrieved from somewhere else, it needs to be unique
                    # and if not, this won't hurt anything
                    piece.id = uuid.uuid4()

                self._memory.add_request_response_to_memory(request=request)
        return conversation_id

    def get_chat_results(self) -> list[dict]:
        """
        Retrieves single-turn results from the orchestrator's memory, pairing each user
        message with the next assistant message in the same conversation. Each result
        entry includes:
          {
            "conversation_id": str,
            "prompt": str,
            "assistant_response": str,
            "scores": [
                {
                    "score_value": float,
                    "score_rationale": str
                },
                ...
            ]
          }

        Returns:
            list[dict]: A list of single-turn results, ready to be used in a single-turn HTML report.
        """
        messages = self.get_memory()
        results = []

        user_prompt = None
        conversation_id = None

        # Iterate through all messages in memory
        for msg in messages:
            if msg.role == "user":
                # Record user prompt and conversation ID
                user_prompt = msg.converted_value
                conversation_id = msg.conversation_id

            elif msg.role == "assistant" and user_prompt is not None:
                # We have found an assistant response that pairs with the last user prompt
                assistant_response = msg.converted_value

                # Convert the message scores to a list of dicts
                single_turn_scores = []
                for s in msg.scores:
                    single_turn_scores.append({
                        "score_value": s.score_value,
                        "score_rationale": s.score_rationale
                    })

                # Build the single-turn result
                results.append({
                    "conversation_id": conversation_id,
                    "prompt": user_prompt,
                    "assistant_response": assistant_response,
                    "scores": single_turn_scores
                })

                # Reset for the next user->assistant pair
                user_prompt = None
                conversation_id = None

        return results
