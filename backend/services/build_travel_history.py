from models import PageExtractionResponse, ExtractedFields, StampRecord, StayResponse, TravelHistoryResponse
from collections import defaultdict
from datetime import datetime
import uuid

MOCK_EXTRACTION_RESULTS = [
    ExtractedFields(
        date="2016-07-04",
        country=None,
        direction=None,
        raw_text="4 Jul 2016",
        extraction_confidence=0.4,
    ),
    ExtractedFields(
        date="2017-08-21",
        country="GBR",
        direction="ENTRY",
        raw_text="IMMIGRATION OFFICER HEATHROW (5) 21 AUG 2017 (51091)",
        extraction_confidence=0.85,
    ),
    ExtractedFields(
        date="2016-06-26",
        country="THA",
        direction="ENTRY",
        raw_text="IMMIGRATION SUVARNABHUMI AIRPORT THAILAND VISACLASS ORO 26 JUN 2016 ADMITTED UNTIL 25 JUL 2016 SIGNED",
        extraction_confidence=0.85,
    ),
    ExtractedFields(
        date="2018-11-24",
        country="THA",
        direction="ENTRY",
        raw_text="IMMIGRATION BANGKOK THAILAND VISACLASS 24 NOV 2018 ADMITTED UNTIL 23 DEC 2018 SIGNED",
        extraction_confidence=0.85,
    ),
    ExtractedFields(
        date="2018-12-24",
        country="SGP",
        direction="EXIT",
        raw_text="4 DEC 2018 REMAIN IN SINGAPORE NINETY DAYS FOR VISIT ONLY",
        extraction_confidence=0.6,
    ),
    ExtractedFields(
        date="2018-11-17",
        country="THA",
        direction="ENTRY",
        raw_text="MMIGRATION SUVARNABHUMI AIRPORT VISACLASS 17 NOV 2018 ADMITTED UNTIL 16 DEC 2018 SIGNED",
        extraction_confidence=0.8,
    ),
    ExtractedFields(
        date="2018-12-25",
        country="THA",
        direction="EXIT",
        raw_text="IMMIGRATION DEPARTED 25 DEC 2018",
        extraction_confidence=0.7,
    ),
    ExtractedFields(
        date="2018-11-21",
        country="THA",
        direction="EXIT",
        raw_text="IMMIGRATION DEPARTED BANGKOK 21 NOV 2018",
        extraction_confidence=0.7,
    ),
    ExtractedFields(
        date="2018-11-25",
        country="THA",
        direction="EXIT",
        raw_text="IMMIGRATION DEPARTED SUVARNABHUMI AIRPORT THAILAND 25 NOV 2018 SIGNED",
        extraction_confidence=0.85,
    ),
    ExtractedFields(
        date=None,
        country=None,
        direction=None,
        raw_text=None,
        extraction_confidence=0.1,
    ),
    ExtractedFields(
        date="2018-11-24",
        country="KHM",
        direction="EXIT",
        raw_text="CAMBODIA IMMIGRATION SIEM REAP AIRPORT DEPARTED 24 NOV 2018 CODE: 20",
        extraction_confidence=0.85,
    ),
    ExtractedFields(
        date=None,
        country=None,
        direction=None,
        raw_text=None,
        extraction_confidence=0.1,
    ),
    ExtractedFields(
        date="2018-11-21",
        country="KHM",
        direction="ENTRY",
        raw_text="IMMIGRATION CAMBODIA SIEM REAP AIRPORT PERMITTED 21 NOV 2018 UNTIL 21 DEC 2018 CODE: S111 21",
        extraction_confidence=0.85,
    ),
    ExtractedFields(
        date=None,
        country=None,
        direction=None,
        raw_text="KINGDOM OF CAMBODIA Siem Reap Visa No. 16093329 Issuing Post: Siem Reap Surname: WILSON Given Name: TEE Passport Number: SS1321349 Entries: Single Expiry Date: Employment Not Permitted 21 DEC 2018 Issue Date: 21 NOV 2018 Fee: 30USD",
        extraction_confidence=0.7,
    ),
    ExtractedFields(
        date="2016-07-04",
        country="CHN",
        direction="ENTRY",
        raw_text="中国边检 CHINA 2016-07-04 甫宁[入] 0140060",
        extraction_confidence=0.85,
    ),
    ExtractedFields(
        date="2010-11-17",
        country="CHN",
        direction="ENTRY",
        raw_text="中国边检 CHINA 2010-11-17 浦东[入] 0550457",
        extraction_confidence=0.8
    ),
    ExtractedFields(
        date="2018-12-25",
        country="CHN",
        direction="ENTRY",
        raw_text="中国边检 CHINA 2018-12-25 高崎[入] 0110248",
        extraction_confidence=0.85
    ),
    ExtractedFields(
        date="2018-12-25",
        country="CHN",
        direction="EXIT",
        raw_text="中国边检 CHINA 2018-12-25 高崎[出] 0110258/0110259",
        extraction_confidence=0.85
    ),
    ExtractedFields(
        date="2018-11-17",
        country="CHN",
        direction="EXIT",
        raw_text="中国边检 CHINA 2018-11-17 浦东[出] 0551081",
        extraction_confidence=0.85
    ),
    ExtractedFields(
        date="2016-07-17",
        country="CHN",
        direction="EXIT",
        raw_text="中国边检 CHINA 2016-07-17 浦东[出] 0551416",
        extraction_confidence=0.85
    ),
    ExtractedFields(
        date="2016",
        country="CHN",
        direction=None,
        raw_text="CANCELLED 2016 ISSUED AT 签发地点 北京 DURATION OF EACH STAY 每次停留期限 060 天 DAYS AFTER ENTRY 护照号码 PASSPORT NO. 5513217 JIE LUN TEE",
        extraction_confidence=0.6
    ),
    ExtractedFields(
        date=None,
        country="CHN",
        direction=None,
        raw_text="21349",
        extraction_confidence=0.3
    ),
    ExtractedFields(
        date="2019-01-04",
        country="CHN",
        direction="EXIT",
        raw_text="中国边检 CHINA 2019-01-04 萬岛机场[出] 0210035",
        extraction_confidence=0.8
    ),
    ExtractedFields(
        date="2019-01-02",
        country="CHN",
        direction="ENTRY",
        raw_text="中国边检 CHINA 2019-01-02 [入] 0040103",
        extraction_confidence=0.65
    ),
    ExtractedFields(
        date="2019-11-23",
        country="CHN",
        direction="ENTRY",
        raw_text="中国边检 CHINA 2019-11-23 西安[入] 0180078",
        extraction_confidence=0.85
    ),
    ExtractedFields(
        date="2018-12-25",
        country="IDN",
        direction="ENTRY",
        raw_text="Visas IMMIGRATION INDONESIA VISA EXEMPTION NGURAH RAI 25 DEC 2018 PERMITTED TO ENTER AND STAY FOR 30 DAYS FROM DATE SHOWN ABOVE \"WORK PROHIBITED\" \"NOT EXTENDABLE\" ART 41 ACT 6 2011",
        extraction_confidence=0.85
    ),
    ExtractedFields(
        date="2019-11-30",
        country="CHN",
        direction="EXIT",
        raw_text="中国边检 CHINA 2019-11-30 重庆[出] 0220219",
        extraction_confidence=0.85
    ),
    ExtractedFields(
        date="2018-12-28",
        country="IDN",
        direction="EXIT",
        raw_text="IMMIGRATION INDONESIA DEPARTURE 28 DEC '18 ART. 15 ACT. 6. 2011",
        extraction_confidence=0.85
    ),
    ExtractedFields(
        date="2017-08-21",
        country=None,
        direction=None,
        raw_text="21.08.17 88",
        extraction_confidence=0.4
    ),
    ExtractedFields(
        date="2017-08-12",
        country=None,
        direction=None,
        raw_text="12.08.17 26 SAYARAS JUAV",
        extraction_confidence=0.35
    ),
]


MOCK_STAMPS = []

for i, extracted_fields in enumerate(MOCK_EXTRACTION_RESULTS):
    stamp = StampRecord(
        stamp_id=str(i),
        stamp_image="",
        bounding_box=[],
        mask=None,
        detection_confidence=0.6,
        extracted_fields=extracted_fields,
        page_source="",
        page_number=i
    )
    MOCK_STAMPS.append(stamp)


def stay_response_sort_key(stay: StayResponse) -> datetime:
    if stay.entry_date is not None:
        return datetime.strptime(stay.entry_date , "%Y-%m-%d")
    else:
        return datetime.strptime(stay.exit_date , "%Y-%m-%d")


def is_valid_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def build_travel_history(pages: list[PageExtractionResponse]) -> TravelHistoryResponse:
    stamps_by_country: dict[str, list[StampRecord]] = defaultdict(list)

    all_stamps: list[StampRecord] = []
    for page in pages:
        all_stamps.extend(page.stamps)

    if len(pages) == 0:
        all_stamps = MOCK_STAMPS

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
    
