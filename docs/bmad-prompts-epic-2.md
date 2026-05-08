# Epic-2 : Data Scrapper Agents
# List of BMAD Prompts

This document enlists the list of prompts fed into BMAD Framework.

## Planning Phase

### Update Project Brief

@bmad-agent-analyst Based on the updated Project Brief, confirm the **data collection policy** for Epic 2:
- We will target UK comparison/editorial-aggregation sources (e.g., **Moneyfacts**, **MoneySavingExpert**) for discovery/monitoring.
- We will treat **provider product pages** as the source of truth for terms whenever feasible.
- Cadence: **every 6 hours** for monitored pages, plus a **daily full refresh**, plus an **admin-only on-demand** refresh.
- Freshness SLA: aim for **median ≤ 6 hours**, and flag tables if last checked is **> 24 hours**.

### Update PRD

@bmad-agent-pm Update the **PRD** based on the revised Project Brief. We are using **Firecrawl** for scraping UK financial sites. Add requirements for: 1. Storing "Last Checked" timestamps, 2. A background process for the 6-hour refresh cadence, and 3. An admin button in the UI to trigger an on-demand refresh

### Update Architecture Document

@bmad-agent-architect Update the **Architecture Document** to include the new **Scraper Service** design. We are using **Firecrawl** for ingestion and **SQLite** for storage. Please define: 1. Schema updates for 'Last Checked' and 'Source URL' fields, 2. The Python service structure for the 6-hour cron/background job, and 3. How the frontend will trigger an on-demand refresh via the FastAPI backend.


## Implementation Phase

### Sprint Planning (Epic-2)

@bmad-agent-pm Run **Sprint Planning** for **Epic 2**. Please create the epic-2-data-scrapper-agents.md file and update sprint-status.yaml. Break down the Scraper Service requirements into logical stories, starting with the Firecrawl integration and ending with the UI refresh button. 

#### 2-1-firecrawl-integration-scraper-base

@bmad-agent-developer I am ready to start **Epic 2**. Mark **Story 2.1** (Firecrawl Client Setup) as **in-progress**. Please create a Python service that uses the Firecrawl API to scrape a sample UK savings page. We need to ensure it can extract the bank name and interest rate into a structured JSON format. I have my API key ready.

#### 2-2-target-uk-site-parser-moneysavingexpert-or-moneyfacts

The Firecrawl client is working! Please mark Story 2.1 as done and move to Story 2.2: Data Integration Service. Create a service that takes the JSON output from the scraper and updates our SQLite database. It should handle 'Upserts'—meaning it updates existing bank rates if they've changed and adds new ones if they don't exist yet. Make sure it also saves the 'Last Checked' timestamp.

* Cursor suggested couple of improvement/tightening steps and I allowed it to proceed with those.

Let's proceed with Story 2.2. Create the Data Integration Service to map scraped results to both the Fixed Savings and ISA tables. Ensure the 'Upsert' logic correctly identifies existing products in each category to avoid duplicates. Also, make sure the last_checked timestamp and source_url are updated for every record processed

Finish Story 2-2. Ensure the parser accurately extracts the interest rates and product names for both Fixed Savings and ISAs from the target site. Once the parser is validated, mark Story 2-2 as done.

#### 2-3-sqlite-upsert-pipeline-last-checked-and-sources

Proceed to Story 2-3: SQLite Upsert Pipeline. Implement the logic to:Match incoming scraped data against existing records (using Bank Name + Product Type).Update the rate if it has changed.Always update the last_checked timestamp.Insert new products if they don't exist.

#### 2-4-background-refresh-service-6-hour-and-daily

@bmad-agent-developer Mark **Story 2.3** as **done** in sprint-status.yaml. Now, proceed to **Story 2.4: Background Refresh Service**. Implement a background task (using a library like APScheduler or a dedicated background thread) that runs the scraper and upsert pipeline every **6 hours**. Ensure it logs its progress and handles errors gracefully so it doesn't crash the main FastAPI app.

#### 2-5-admin-refresh-endpoints-fastapi

@bmad-agent-developer Mark **Story 2.4** as **done** in sprint-status.yaml. Now, proceed to **Story 2.5: Admin Refresh Endpoints**. Create a FastAPI endpoint (e.g., POST /admin/refresh) that manually triggers the same scraper and upsert pipeline used by the background service. Ensure it returns a success message once the update is complete so the frontend knows when to stop the loading state.

#### 2-6-frontend-admin-refresh-button

@bmad-agent-developer Mark **Story 2.5** as **done** in sprint-status.yaml. Now, proceed to **Story 2.6: Frontend Admin Refresh Button.** Add a "Refresh Live Rates" button to the dashboard (position it clearly, e.g., near the filters).Implement a loading state (spinner or progress text) so I know the scraping is happening.Ensure the tables re-fetch/auto-refresh their data once the API returns a success response.

#### epic-2-retrospective

@bmad-agent-qa Run the **Epic 2 Retrospective**. Please review the scraper logic, the SQLite upsert pipeline, and the background service. Check that the last_checkedtimestamps are updating correctly, update sprint-status.yaml to mark **Epic 2** as **done**, and suggest any refinements for data accuracy in the next phase.