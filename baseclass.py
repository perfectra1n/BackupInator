import json

# Local import
import log
import requests
import tempfile
from requests.adapters import HTTPAdapter, Retry

class BaseBackupClass():
    def __init__(self, debug=False) -> None:
        self.logger = log.get_logger(__file__, debug=debug)
        self.config = self.get_config()

    def get_config(self, file:str="config.json") -> dict:
        """Gets the config file and returns it as a dict.

        Returns
        -------
        dict
            The config file as a dict.
        """
        with open(file, "r") as f:
            config = json.load(f)
        return config

    def save_config(self) -> None:
        pass
    
    def validate_config(self, required_keys:list=[], system:str="") -> bool:
        if not all(key in required_keys for key in self.config[system]):
            self.logger.error("Missing required keys in config file")
            self.logger.error(f"Keys that might be missing: {required_keys}")
            self.logger.error(f"Compared them against: {self.config[system]}")
            self.logger.info("Please check the config file and try again")
            
            return False
    
    def put_data_in_tempfile(self, data: bytes) -> str:
        """
        Creates a temporary file and writes data to it.

        :param data: The data to write to the file.
        :return: The path to the temporary file.
        """
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(data)
            return f.name
        
    def get_requests_session(self) -> requests.Session:
        """Creates a requests session with the token and user agent header."""
        session = requests.Session()

        # Version here

        # Set up retry logic
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])

        # Have it work for both http and https
        session.mount("https://", HTTPAdapter(max_retries=retries))
        session.mount("http://", HTTPAdapter(max_retries=retries))
        
        return session

    def set_url(self, url=""):
        """Sets the URL for the session.

        Parameters
        ----------
        url : str, optional
            The URL to set for the session, by default ""
        """
        if url != "":
            self.url = url
        if url == "" and self.url == "":
            raise ValueError("URL cannot be empty")

    def set_session_auth(self, token: str) -> None:
        """Sets the authorization token for the session.

        Parameters
        ----------
        token : str
            The token to set for the session.
        """
        self.session.headers.update({"Authorization": token})

    def make_request(self, url:str, api_endpoint: str, method="GET", data="", params={}) -> requests.Response:
        """Standard request method for making requests.

        Parameters
        ----------
        api_endpoint : str
            The API endpoint to make the request to. This should not include the URL or the /etapi prefix.
        method : str, optional
            The HTTP method to use, by default "GET"
        data : str, optional
            The body data to send with the request, by default ""
        params : dict, optional
            The parameters to include in the API call, by default {}

        Returns
        -------
        requests.Response
            The response from the Trilium API.
        """
        # We use our own session that holds the token, so we shouldn't
        # need to enforce it here.

        request_url = url + api_endpoint
        req_resp = self.session.request(method, request_url, data=data, params=params)
        if req_resp.status_code not in self.valid_response_codes:
            self.logger.warning(
                f"Possible invalid response code: {str(req_resp.status_code)}, response text: {req_resp.text}"
            )
        return req_resp
    
            