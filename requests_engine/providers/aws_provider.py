import json
import botocore
import aiohttp
from requests_engine.conversation import Conversation
import botocore.session
from botocore.awsrequest import AWSRequest
from botocore.auth import SigV4Auth

class AwsProvider:
    def __init__(
        self,
        credential_file_path: str,
        model_id: str = "anthropic.claude-3-haiku-20240307-v1:0",
        region: str = "us-west-2",
    ):
        self.session = botocore.session.get_session()

        with open(credential_file_path) as file:
            contents = json.load(file)
            self.session.set_credentials(contents["key"], contents["secret"])

        self.model_id = model_id
        self.region = region

    def get_request_body(self, system_message: str, messages: Conversation, temperature: float) -> str:
        return json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "system": system_message,
                "messages": messages.messages,
                "temperature": temperature,
            }
        )

    def get_inference_request(
        self, aiohttp_session: aiohttp.ClientSession, request_body: str
    ):
        # Creating an AWSRequest object for a POST request with the service specified endpoint, JSON request body, and HTTP headers
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-runtime/client/invoke_model.html
        # https://docs.anthropic.com/claude/reference/messages_post
        request = AWSRequest(
            method="POST",
            url=f"https://bedrock-runtime.{self.region}.amazonaws.com/model/{self.model_id}/invoke",
            data=request_body,
            headers={"content-type": "application/json"},
        )

        # Adding a SigV4 authentication information to the AWSRequest object, signing the request
        sigv4 = SigV4Auth(self.session.get_credentials(), "bedrock", self.region)
        sigv4.add_auth(request)

        # Prepare the request by formatting it correctly
        prepped = request.prepare()

        print("Sending POST request to AWS Bedrock endpoint")

        return aiohttp_session.post(
            prepped.url, data=request_body, headers=prepped.headers
        )

    def get_1k_token_input_output_cost(self) -> dict:
        if self.model_id == "anthropic.claude-3-haiku-20240307-v1:0":
            return {
                "input": 0.00025,
                "output": 0.00125,
            }
