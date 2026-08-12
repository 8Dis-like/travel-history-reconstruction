from models import PageExtractionResponse, ExtractedFields, StampRecord, StayResponse, TravelHistoryResponse
from collections import defaultdict
from datetime import datetime, timezone
import uuid
from helpers import is_valid_date


def stay_response_sort_key(stay: StayResponse) -> datetime:
    if stay.entry_date is not None:
        return datetime.strptime(stay.entry_date , "%Y-%m-%d")
    else:
        return datetime.strptime(stay.exit_date , "%Y-%m-%d")


""" def is_valid_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False """


def build_travel_history(stamps: dict[str, StampRecord]) -> TravelHistoryResponse:
    stamps_by_country: dict[str, list[StampRecord]] = defaultdict(list)

    all_stamps: list[StampRecord] = list(stamps.values())

    unattributable_stamps: list[StampRecord] = []

    for stamp in all_stamps:
        country = stamp.extracted_fields.country
        date = stamp.extracted_fields.date
        if country is not None and date is not None and is_valid_date(date):
            stamps_by_country[country].append(stamp)
        else:
            unattributable_stamps.append(stamp)

    stay_responses = []

    for country, stamps in stamps_by_country.items():
        stamps_by_date = sorted(stamps, key=lambda s: datetime.strptime(s.extracted_fields.date, "%Y-%m-%d"))

        stay_response = None

        for stamp in stamps_by_date:
            date = stamp.extracted_fields.date
            direction = stamp.extracted_fields.direction

            if direction is not None:
                if direction.upper() == "ENTRY":
                    if stay_response is None:
                        stay_response = StayResponse(
                            stay_id=str(uuid.uuid4()),
                            country=country,
                            entry_date=date,
                            exit_date=None,
                            entry_stamp=stamp,
                            exit_stamp=None,
                            status="confirmed",
                            flags=[]
                        )
                    else:
                        stay_response.status = "flagged"
                        stay_response.flags.append("No exit detected")
                        stay_responses.append(stay_response)

                        stay_response = StayResponse(
                            stay_id=str(uuid.uuid4()),
                            country=country,
                            entry_date=date,
                            exit_date=None,
                            entry_stamp=stamp,
                            exit_stamp=None,
                            status="confirmed",
                            flags=[]
                        )
                elif direction.upper() == "EXIT":
                    if stay_response is not None:
                        stay_response.exit_date = date
                        stay_response.exit_stamp = stamp
                        stay_responses.append(stay_response)

                        stay_response = None
                    else:
                        stay_responses.append(
                            StayResponse(
                                stay_id=str(uuid.uuid4()),
                                country=country,
                                entry_date=None,
                                exit_date=date,
                                entry_stamp=None,
                                exit_stamp=stamp,
                                status="flagged",
                                flags=["No entry detected"]
                            )
                        )
            else:
                if stay_response is None:
                    stay_response = StayResponse(
                        stay_id=str(uuid.uuid4()),
                        country=country,
                        entry_date=date,
                        exit_date=None,
                        entry_stamp=stamp,
                        exit_stamp=None,
                        status="inferred",
                        flags=["Direction unreadable, entry assumed"]
                    )
                else:
                    stay_response.exit_date = date
                    stay_response.exit_stamp = stamp
                    stay_response.status="inferred"
                    stay_response.flags.append("Direction unreadable, exit assumed")
                    stay_responses.append(stay_response)

                    stay_response = None

        if stay_response is not None:
            stay_response.status = "flagged"
            stay_response.flags.append("No exit detected")
            stay_responses.append(stay_response)
            stay_response = None

    sorted_stay_responses: list[StayResponse] = sorted(stay_responses, key=stay_response_sort_key)

    if sorted_stay_responses and sorted_stay_responses[-1].exit_date is None:
        if "No exit detected" in sorted_stay_responses[-1].flags:
            sorted_stay_responses[-1].status = "confirmed"
            sorted_stay_responses[-1].flags.remove("No exit detected")
        sorted_stay_responses[-1].flags.append("ongoing")
            

    return TravelHistoryResponse(
        stays=sorted_stay_responses, unattributable_stamps=unattributable_stamps
    )

if __name__ == "__main__":
    travel_response = build_travel_history([])
    for stay in travel_response.stays:
        print(f"{stay.country}: Entry({stay.entry_date})-Exit({stay.exit_date})")

    print(travel_response.unattributable_stamps)
    
