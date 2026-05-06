# Epic-1 : Foundation — SQLite database + basic React tables
# List of BMAD Prompts

This document enlists the list of prompts fed into BMAD Framework.

## Planning Phase

### Generate Project Brief

@bmad-agent-analyst Please help me create a **Project Brief** for my UK Savings & ISA Rate Tracker. Focus on identifying the key features we need to show the best fixed rates and ISA rates from UK banks.

### Generate PRD

@bmad-agent-pm Create a **PRD** (Product Requirements Document) based on the Project Brief we just finished. Make sure to include "User Stories" for viewing fixed-rate savings and ISA tables.

### Generate Architecture Document

@bmad-agent-architect Create the **Architecture Document** based on our PRD. I have decided to use **SQLite** instead of Supabase for the database. Please design the SQLite schema for storing UK savings rates and ISA data, and outline the Python backend structure for local data management.

## Implementation Phase

### Sprint Planning (Epic-1)

@bmad-agent-pm Run the **Sprint Planning** workflow. Please look at our Architecture.mdandPRD.mdto create asprint-status.yaml file. This file should list the initial tasks (User Stories) needed to set up the SQLite database and the basic React frontend.

#### epic-1: 1-1-add-sqlite-schema-bootstrap

@bmad-agent-developer I am ready to start **Epic 1**. Please look at the first story in epic-1.md (likely project initialization). Execute that story by setting up the folder structure, initializing the Python virtual environment, and creating the basic React/Tailwind template.

#### epic-1: 1-2-python-backend-skeleton-local-data-management

Yes, please update the sprint-status.yaml to mark Story 1.1 as complete, and then proceed with **Story 1.2** to create the FastAPI app and the SQLite database connection helpers.

#### epic-1: 1-3-seed-data-loader-local-json-csv-sqlite

Actually, let's stick to the backlog order. Please mark Story 1-2 as done, and then move to Story 1-3: Seed Data Loader. We need to get some sample UK savings and ISA data into the SQLite database first so we can verify the API later.

#### epic-1: 1-4-table-query-endpoints-fixed-savings-cash-isa

Go ahead. Mark Story 1-3 as done and proceed to Story 1-4: Table query endpoints. Create the FastAPI routes to fetch and filter the fixed savings and Cash ISA data from the database. Let's make sure we can verify them with a simple browser test afterwards.

#### epic-1: 1-5-react-app-scaffold-routing

@bmad-agent-developer Mark **Story 1-4** as **done** in sprint-status.yaml. Now, proceed to **Story 1-5: React app scaffold & routing**. Set up the React frontend using Tailwind CSS and create a basic navigation menu to switch between the 'Fixed Rate' and 'ISA' views.

#### epic-1: 1-6-react-table-ui-mvp-fields

he routing works great! Mark Story 1-5 as done. Now, let's move to Story 1-6: React table UI MVP. Create a table component that fetches the data from our FastAPI backend and displays the bank name, interest rate, and term for both the Fixed Savings and ISA pages. Use Tailwind to make it look clean.

#### epic-1: 1-7-filters-ui-api-wiring

The tables look great. Mark Story 1-6 as done. Now, proceed to Story 1-7: Filters UI & API Wiring. Add dropdowns or buttons to the frontend so I can filter the results (e.g., by 1-year or 2-year terms). Update the React code to send these filters to the FastAPI backend we built.

#### epic-1: 1-8-basic-styling-accessibility-pass

Filters are working perfectly! Mark Story 1-7 as done. Now, proceed to Story 1-8: Basic Styling & Accessibility Pass. Use Tailwind to make the tables look professional (e.g., hover states, clear headers, currency formatting). Ensure the layout looks good on mobile and add basic accessibility like ARIA labels for the filters.

#### epic-1: retrospective

@bmad-agent-qa Run the **Epic 1 Retrospective**. Please review the code created so far against our PRD.md. Check for any bugs or missing features from the original plan, update sprint-status.yaml to mark Epic 1 as **done**, and suggest any improvements for the next phase.

