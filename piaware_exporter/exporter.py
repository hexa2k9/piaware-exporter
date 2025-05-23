import logging
from prometheus_client import Enum, Counter, Gauge
import requests
import time

logger = logging.getLogger()


class PiAwareMetricsExporter:
    """Fetches status from PiAware, generates Prometheus metrics with that data, and
    exports them to an endpoint.
    """

    def __init__(self, host, port, fetch_interval, proto="http"):
        self.piaware_status_url = f"{proto}://{host}:{port}"
        self.fetch_interval = fetch_interval

        # Prometheus metrics to collect and expose
        self.radio_state = Enum(
            "piaware_radio_state",
            "Radio Status",
            states=["green", "amber", "red", "N/A"],
        )
        self.piaware_state = Enum(
            "piaware_service_state",
            "PiAware Service Status",
            states=["green", "amber", "red", "N/A"],
        )
        self.flightaware_connection_state = Enum(
            "piaware_connect_to_flightaware_state",
            "FlightAware Connection Status",
            states=["green", "amber", "red", "N/A"],
        )
        self.mlat_state = Enum(
            "piaware_mlat_state", "MLAT Status", states=["green", "amber", "red", "N/A"]
        )
        self.gps_state = Enum(
            "piaware_gps_state", "GPS Status", states=["green", "amber", "red", "N/A"]
        )

    def start_fetch_loop(self):
        """Main loop to do periodic fetches of piaware status.json"""
        while True:
            self.fetch_piaware_status()
            time.sleep(self.fetch_interval)

    def fetch_piaware_status(self):
        """Fetch piaware status.json and update Prometheus metric"""
        try:
            piaware_status_url = f"{self.piaware_status_url}/status.json"
            response = requests.get(url=piaware_status_url, params={"ts": time.time()})
        except requests.exceptions.ConnectionError:
            logger.error(f"Could not connect to {self.piaware_status_url}")
            return
        except requests.exceptions.Timeout:
            logger.error(f"Timeout Error requesting {self.piaware_status_url}")
            return
        except Exception as e:
            logger.error(f"Error reading piaware status.json: {e}")
            return

        if 200 < response.status_code >= 300:
            # Non 200 response code received reading piaware status.json
            logger.error(
                f"GET {piaware_status_url} - Response: {response.status_code} - ERROR"
            )
            self.piaware_state.state("N/A")
            self.flightaware_connection_state.state("N/A")
            self.mlat_state.state("N/A")
            self.radio_state.state("N/A")
            self.gps_state.state("N/A")
            return

        logger.info(f"GET {piaware_status_url} - Response: {response.status_code} - OK")

        request_json = response.json()

        piaware = request_json.get("piaware")
        flightaware_connection = request_json.get("adept")
        mlat = request_json.get("mlat")
        radio = request_json.get("radio")
        gps = request_json.get("gps")

        if piaware:
            status = piaware.get("status")
            if status == "green":
                self.piaware_state.state("green")
            elif status == "amber":
                self.piaware_state.state("amber")
            else:
                self.piaware_state.state("red")

        if flightaware_connection:
            status = flightaware_connection.get("status")
            if status == "green":
                self.flightaware_connection_state.state("green")
            elif status == "amber":
                self.flightaware_connection_state.state("amber")
            else:
                self.flightaware_connection_state.state("red")

        if mlat:
            status = mlat.get("status")
            if status == "green":
                self.mlat_state.state("green")
            elif status == "amber":
                self.mlat_state.state("amber")
            else:
                self.mlat_state.state("red")

        if radio:
            status = radio.get("status")
            if status == "green":
                self.radio_state.state("green")
            elif status == "amber":
                self.radio_state.state("amber")
            else:
                self.radio_state.state("red")

        if gps:
            status = gps.get("status")
            if status == "green":
                self.gps_state.state("green")
            elif status == "amber":
                self.gps_state.state("amber")
            else:
                self.gps_state.state("red")
