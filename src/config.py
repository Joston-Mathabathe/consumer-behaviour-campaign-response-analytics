"""Central configuration: paths, modelling constants and business assumptions."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "bank-additional-full.csv"
PROCESSED = ROOT / "data" / "processed"
IMAGES = ROOT / "images"

RANDOM_STATE = 42
TEST_SIZE = 0.20

# Variables only known AFTER a call ends -> never used for pre-call targeting.
LEAKY = ["duration"]

# Business assumptions (illustrative, editable). The dataset has no cost or
# revenue fields, so these are explicit scenario inputs, not facts.
COST_PER_CALL = 5.0           # fully loaded cost of one outbound contact attempt
VALUE_PER_SUBSCRIBER = 150.0  # contribution margin from one term-deposit customer
