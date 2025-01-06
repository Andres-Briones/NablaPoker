import json
from pathlib import Path
from .hand import Hand

class Session:
    def __init__(self, session_id: str, site_name: str = "Unknown", network_name: str = "Unknown", internal_version: str = "Unkwown", spec_version: str = "1.4.6"):
        self.session_id = session_id
        self.site_name = site_name
        self.network_name = network_name
        self.internal_version = internal_version
        self.spec_version = spec_version
        self.hands : List[Hand] = []

    def add_hand(self, hand: Hand):
        """Add a Hand object to the session."""
        self.hands.append(hand)

    def save_to_OHH(self, output_dir: str, output_stem = None):
        """Save the session data as an OHHfile."""
        if output_stem is None: output_stem = "session_" + str(self.session_id)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{output_stem}.OHH"
        with open(output_file, "w") as outfile:
            for hand in self.hands :
                json.dump(hand.to_json(self), outfile, indent=2, default=str)
                outfile.write("\n\n")
