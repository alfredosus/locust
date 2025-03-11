from locust import HttpUser, between, events, task

import json
import os

from flask import request

BASE_URL = os.getenv("HOST", "localhost")


class OllamaUser(HttpUser):
    wait_time = between(1, 2)  # Simulates users waiting 1-2 seconds between task
    host = f"http://{BASE_URL}:11434/"

    # @task
    # def send_request(self):
    #     data = {
    #         "model": "llama3.1:8b",
    #         "prompt": "Tell me a joke",
    #         "stream": False
    #     }
    #     response = self.client.post("/api/generate", json=data)
    #     print(response.json()['response'])

    @task
    def apply_stream(self):
        data = {"model": "llama3.1:8b", "prompt": "Tell me a joke", "stream": True}

        with self.client.post("/api/generate", json=data, stream=True, catch_response=True) as response:
            exception = None
            try:
                streamed_text = ""

                # Read response stream in chunks
                for chunk in response.iter_content(chunk_size=1024):  # Read 1KB chunks
                    if chunk:
                        chunk_text = chunk.decode("utf-8")
                        streamed_text += chunk_text

                        # print(chunk_text, end="", flush=True)  # Print real-time output

                response.success()
                # json_resp = json.loads(chunk_text)
                # if not hasattr(self, "numeric_keys"):
                #     self.numeric_keys = [key for key, value in json_resp.items() if isinstance(value, numbers.Number)]
                # extra_metrics = {key: value for key, value in json_resp.items() if key in self.numeric_keys}

                # request_meta = {
                #     "request_type": "ollama",
                #     "name": "alfredo",
                #     "start_time": datetime.fromisoformat(json_resp.get("created_at").rstrip("Z")).timestamp(),
                #     "response_time": int(json_resp.get("total_duration")) / 1_000_000,
                #     "extra_metrics": extra_metrics,
                #     "response_length": 0,  # calculating this for an xmlrpc.client response would be too hard
                #     "response": None,
                #     "context": {"foo": "bar"},  # see HttpUser if you actually want to implement contexts
                #     "exception": None,
                # }
                # self.environment.events.request.fire(**request_meta)
            except Exception as e:
                response.failure(f"Streaming error: {e}")
                print(e)


locust_env = None


@events.init.add_listener
def locust_init(environment, **kwargs):
    if environment.web_ui:
        global locust_env
        locust_env = environment

        @environment.web_ui.app.after_request
        def extend_stats_response(response):
            if request.path != "/stats/requests":
                return response

            # Load response data as a dictionary
            response_data = response.get_json()

            # for stat in locust_env.stats:
            #     # Retrieve the context stored inside the request
            #     if hasattr(stat, "context"):
            #         stat["context"] = stat.context

            # # Modify each item in the "stats" array
            # for stat in response_data["stats"]:
            #     stat["custom_metric"] = stat["num_requests"] * 2  # Example modification

            # Update the response
            response.set_data(json.dumps(response_data))

            return response
