import requests
import pandas as pd
import time
import math
from datetime import datetime, timezone
from api_keys_jobs import URL_JOOBLE, API_KEY_JOOBLE, APP_ID_ADZUNA, APP_KEY_ADZUNA

def getJoobleData():
    # ============================================================
    # 1. JOOBLE CONFIG
    # ============================================================
    headers = {"Content-Type": "application/json"}
    # ============================================================
    # 2. RESEARCH PARAMETERS
    # ============================================================
    positions = [
        "Data Analyst",
        "Data Scientist",
        "Data Engineer"
    ]
    cities = [
        "Toronto, ON",
        "Vancouver, BC",
        "Montreal, QC"
    ]
    # Radius of search in km
    RADIUS = "26"

    # Number of jobs requested per page
    RESULTS_PER_PAGE = 100

    # Maximum number of pages allowed per position-city combination
    # CHANGE THIS TO 20 TO GET 2000 (20 x 100) JOB POSTING PER EACH POSITION X CITY
    MAX_PAGES = 25

    # Delay between API requests
    REQUEST_DELAY = 2.5

    # ============================================================
    # 3. STORAGE
    # ============================================================
    all_jobs = []

    # ============================================================
    # 4. LOOP THROUGH POSITIONS AND CITIES
    # ============================================================
    for position in positions:
        for city in cities:
            print("\n" + "=" * 70)
            print(f"Starting search: {position} | {city}")
            print("=" * 70)
            # ----------------------------------------------------
            # FIRST REQUEST
            # Used to get totalCount and page 1 results
            # ----------------------------------------------------
            first_payload = {
                "keywords": position,
                "location": city,
                "radius": RADIUS,
                "page": 12,
                "ResultOnPage": RESULTS_PER_PAGE
            }
            try:
                response = requests.post(
                    URL_JOOBLE,
                    headers=headers,
                    json=first_payload,
                    timeout=30
                )

                response.raise_for_status()
                data = response.json()
                total_jobs = data.get("totalCount", 0)
                jobs = data.get("jobs", [])
                print(f"Total jobs reported by Jooble: {total_jobs}")

                # Calculate the number of pages actually needed
                # That is the maximum, but in some cases, the returned totalCount
                # may be different from the actual number of pages
                pages_needed = math.ceil(total_jobs / RESULTS_PER_PAGE)
                # Never exceed MAX_PAGES
                pages_to_collect = min(pages_needed, MAX_PAGES)
                print(f"Pages needed: {pages_needed}")
                print(f"Pages that will be collected: {pages_to_collect}")
                # ------------------------------------------------
                # SAVE PAGE 1
                # ------------------------------------------------
                request_datetime = datetime.now(timezone.utc).isoformat()
                for job in jobs:
                    job["search_position"] = position
                    job["search_city"] = city
                    job["request_datetime"] = request_datetime
                    job["source_site"] = "Jooble"
                    all_jobs.append(job)
                print(
                    f"{position} | {city} | "
                    f"Page 1 | Jobs retrieved: {len(jobs)}"
                )
                # If only one page is needed, skip directly
                # to the next city/position combination
                if pages_to_collect <= 1:
                    continue
                time.sleep(REQUEST_DELAY)
                # ------------------------------------------------
                # REQUEST REMAINING PAGES
                # ------------------------------------------------
                for page in range(2, pages_to_collect + 1):
                    payload = {
                        "keywords": position,
                        "location": city,
                        "radius": RADIUS,
                        "page": page,
                        "ResultOnPage": RESULTS_PER_PAGE
                    }
                    try:
                        response = requests.post(
                            URL_JOOBLE,
                            headers=headers,
                            json=payload,
                            timeout=30
                        )
                        response.raise_for_status()
                        page_data = response.json()
                        jobs = page_data.get("jobs", [])
                        print(
                            f"{position} | {city} | "
                            f"Page {page} | Jobs retrieved: {len(jobs)}"
                        )
                        # Extra safety:
                        # stop if the API unexpectedly returns no jobs in some page
                        if len(jobs) == 0:
                            print("No more jobs returned. Stopping early.")
                        # Breaking the loop!
                            break

                        request_datetime = datetime.now(timezone.utc).isoformat()
                        # Adding extra information to the file 
                        for job in jobs:
                            job["search_position"] = position
                            job["search_city"] = city
                            job["request_datetime"] = request_datetime
                            job["source_site"] = "Jooble"
                            all_jobs.append(job)
                        time.sleep(REQUEST_DELAY)
                    except requests.exceptions.RequestException as e:
                        print(
                            f"API error for {position} | "
                            f"{city} | Page {page}: {e}"
                        )
                        continue

            # In case the try fails
            except requests.exceptions.RequestException as e:
                print(
                    f"Initial API request failed for "
                    f"{position} | {city}: {e}"
                )
                continue

    # ============================================================
    # 5. CREATE DATAFRAME
    # ============================================================

    df_jooble = pd.DataFrame(all_jobs)


    # ============================================================
    # 6. DISPLAY SUMMARY
    # ============================================================

    print("\n" + "=" * 70)
    print("COLLECTION COMPLETE")
    print("=" * 70)

    print(f"Total jobs collected: {len(df_jooble)}")
    print(f"Total columns: {len(df_jooble.columns)}")

    if not df_jooble.empty:

        print("\nJobs collected by position and city:")

        print(
            df_jooble.groupby(
                ["search_position", "search_city"]
            ).size()
        )


    # ============================================================
    # 7. SAVE RAW DATA
    # ============================================================

    #output_file = "jooble_raw_jobs.csv"

    #df_jooble.to_csv(
    #    output_file,
    #    index=False,
    #    encoding="utf-8-sig"
    #)
    #print(f"\nCSV saved successfully: {output_file}")
    return df_jooble


def getAdzunaData():
    import requests
    import pandas as pd
    import math
    import time
    from datetime import datetime, timezone


    # ============================================================
    # 1. API CONFIGURATION
    # ============================================================
    COUNTRY = "ca"
    headers = {"Accept": "application/json"}
    # ============================================================
    # 2. RESEARCH PARAMETERS
    # ============================================================

    positions = [
        "Data Analyst",
        "Data Scientist",
        "Data Engineer"
    ]

    cities = [
        "Toronto",
        "Vancouver",
        "Montreal"
    ]
    #For Adzuna, the limit is 50 per page
    RESULTS_PER_PAGE = 50
    #Setting the data from the last 280 days
    MAX_DAYS_OLD = 280
    #Setting radius to 26 km
    DISTANCE = 26
    #Delay between requests to avoid overwhelming the API
    REQUEST_DELAY = 2
    # ============================================================
    # 3. STORAGE
    # ============================================================
    all_jobs = []

    # ============================================================
    # 4. LOOP THROUGH ALL POSITION-CITY COMBINATIONS
    # ============================================================

    for position in positions:
        for city in cities:
            print("\n" + "=" * 70)
            print(f"Starting search: {position} | {city}")
            print("=" * 70)
            # ----------------------------------------------------
            # FIRST REQUEST to get data and calculate the number of pages
            # ----------------------------------------------------
            page = 1
            URL = (
                f"https://api.adzuna.com/v1/api/jobs/"
                f"{COUNTRY}/search/{page}"
            )
            params = {
                "app_id": APP_ID_ADZUNA,
                "app_key": APP_KEY_ADZUNA,
                "results_per_page": RESULTS_PER_PAGE,
                "what": position,
                "where": city,
                "content-type": "application/json",
                "max_days_old": MAX_DAYS_OLD,
                "distance": DISTANCE
            }
            try:
                response = requests.get(
                    URL,
                    params=params,
                    headers=headers,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                total_jobs = data.get("count", 0)
                jobs = data.get("results", [])
                print("Total jobs found:", total_jobs)
                print("Jobs returned on page 1:", len(jobs))
                # Calculate only the pages actually needed
                total_pages = math.ceil(
                    total_jobs / RESULTS_PER_PAGE
                )
                print("Total pages needed:", total_pages)
                # Save page 1
                request_datetime = datetime.now(timezone.utc).isoformat()
                for job in jobs:
                    job["search_position"] = position
                    job["search_city"] = city
                    job["request_datetime"] = request_datetime
                    job["source_site"] = "Adzuna"
                    all_jobs.append(job)
                # If there are no more pages, move to next combination
                if total_pages <= 1:
                    continue

                time.sleep(REQUEST_DELAY)

                # ------------------------------------------------
                # REQUEST REMAINING PAGES
                # ------------------------------------------------
                for page in range(2, total_pages + 1):
                    URL = (
                        f"https://api.adzuna.com/v1/api/jobs/"
                        f"{COUNTRY}/search/{page}"
                    )

                    params = {
                        "app_id": APP_ID_ADZUNA,
                        "app_key": APP_KEY_ADZUNA,
                        "results_per_page": RESULTS_PER_PAGE,
                        "what": position,
                        "where": city,
                        "content-type": "application/json",
                        "max_days_old": MAX_DAYS_OLD,
                        "distance": DISTANCE
                    }
                    try:
                        response = requests.get(
                            URL,
                            params=params,
                            headers=headers,
                            timeout=30
                        )

                        response.raise_for_status()
                        page_data = response.json()
                        jobs = page_data.get("results", [])

                        print(
                            f"{position} | {city} | "
                            f"Page {page} | "
                            f"Jobs retrieved: {len(jobs)}"
                        )

                        # Extra safety to stop if no more jobs are returned
                        if len(jobs) == 0:
                            print(
                                "No more jobs returned. "
                                "Stopping this combination."
                            )
                            break

                        request_datetime = datetime.now(timezone.utc).isoformat()

                        for job in jobs:
                            job["search_position"] = position
                            job["search_city"] = city#                        job["request_datetime"] = request_datetime
                            job["source_site"] = "Adzuna"
                            all_jobs.append(job)
                        time.sleep(REQUEST_DELAY)

                    except requests.exceptions.RequestException as e:
                        print(
                            f"API error for {position} | "
                            f"{city} | Page {page}: {e}"
                        )
                        break

            except requests.exceptions.RequestException as e:
                print(
                    f"Initial API request failed for "
                    f"{position} | {city}: {e}"
                )
                continue


    # ============================================================
    # 5. CREATE DATAFRAME
    # ============================================================
    df_adzuna = pd.json_normalize(all_jobs)

    # ============================================================
    # 6. SUMMARY
    # ============================================================
    print("\n" + "=" * 70)
    print("COLLECTION COMPLETE")
    print("=" * 70)
    print("Total jobs collected:", len(df_adzuna))
    print("Total columns:", len(df_adzuna.columns))

    if not df_adzuna.empty:
        print("\nJobs collected by position and city:")
        summary = (
            df_adzuna
            .groupby(
                ["search_position", "search_city"]
            )
            .size()
            .reset_index(name="jobs_collected")
        )
        print(summary)

    # ============================================================
    # 7. SAVE CSV
    # ============================================================
    #output_file = "adzuna_raw_jobs.csv"
    #df_adzuna.to_csv(
    #    output_file,
    #    index=False,
    #    encoding="utf-8-sig"
    #)
    #print(f"\nCSV saved successfully: {output_file}")
    return df_adzuna