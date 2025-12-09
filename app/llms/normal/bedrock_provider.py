import boto3
import json
import logging
import asyncio
from functools import partial
from app.core.config import settings
from .base import BaseLLM, LLMError

log = logging.getLogger("app.models.llm.bedrock")

class BedrockProvider(BaseLLM):
    def __init__(self):
        try:
            self.client = boto3.client(
                service_name="bedrock-runtime",
                region_name=settings.BEDROCK_REGION,
                aws_access_key_id=settings.BEDROCK_ACCESS_KEY,
                aws_secret_access_key=settings.BEDROCK_SECRET_KEY,
            )
            self.model_id = settings.BEDROCK_MODEL_ID
        except Exception as e:
            log.error(f"Failed to initialize Bedrock client: {e}")
            raise LLMError(f"Bedrock initialization failed: {e}")

    async def complete(self, prompt: str) -> str:
        """
        Complete a simple text prompt.
        """
        messages = [{"role": "user", "content": prompt}]
        return await self._invoke_model(messages)

    async def chat(self, messages: list[dict], tools: list | None = None):
        """
        Chat-style API.
        """
        if tools:
            log.info("Tools provided but Bedrock Llama 3 provider implementation may not support them fully yet.")
        
        content = await self._invoke_model(messages)
        log.info(f"raw contant-->{content}") 
        return content 
        # Mock OpenAI-like response structure
        # class MockMessage:
        #     def __init__(self, content):
        #         self.content = content
                
        # class MockChoice:
        #     def __init__(self, content):
        #         self.message = MockMessage(content)
                
        # class MockResponse:
        #     def __init__(self, content):
        #         self.choices = [MockChoice(content)]

        # log.info(f"Mock {MockResponse(content)}")  
        # return MockResponse(content)

    async def _invoke_model(self, messages: list[dict]) -> str:
        # Format prompt for Llama 3
        formatted_prompt = "<|begin_of_text|>"
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            formatted_prompt += f"<|start_header_id|>{role}<|end_header_id|>\n\n{content}<|eot_id|>"
        
        formatted_prompt += "<|start_header_id|>assistant<|end_header_id|>\n\n"

        body = {
            "prompt": formatted_prompt,
            "max_gen_len": 2048,
            "temperature": 0.5,
            "top_p": 0.9,
        }

        try:
            # Run blocking boto3 call in a thread pool
            log.info(f"bedrock llm calling")
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                partial(
                    self.client.invoke_model,
                    modelId=self.model_id,
                    body=json.dumps(body)
                )
            )
            log.info(f"raw data from llm----{response}")
            response_body = json.loads(response.get("body").read())
            log.info(f"response_body data from llm----{response_body}")
            generation = response_body.get("generation")
            log.info(f"generation data from llm----{generation}")
            return generation
            
        except Exception as e:
            log.error(f"Bedrock invocation failed: {e}")
            raise LLMError(f"Bedrock invocation failed: {e}")
