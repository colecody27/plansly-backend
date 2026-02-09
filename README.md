<p align="center">
  <img src="https://plansly.co/logo.svg" alt="Plansly Logo" width="300"/>
</p>

<h1 align="center">Plansly</h1>
<!-- <p align="center">
  Collaborative Planning Platform
</p> -->

<p align="center">
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.9%2B-blue" />
  </a>
  <img src="https://img.shields.io/badge/Flask-Backend-green" />
  <img src="https://img.shields.io/badge/Status-Active%20Development-blue" />
  <a href="https://plansly.co">
    <img src="https://img.shields.io/badge/App-plansly.co-brightgreen" />
  </a>
</p>


<!-- [![Status](https://img.shields.io/badge/Status-WIP-yellow)]() -->
---
## 💡 Overview

> **Plansly** is a lightweight collaboration platform for coordinating trips, events, and shared purchases.  
> It reduces coordination friction by combining planning, collaboration, and payment tracking into a single workflow.

Planning group activities is typically fragmented across messaging apps, spreadsheets, payment apps, and calendars. Plansly centralizes this workflow into a single collaborative environment.

Organizers create a plan and invite participants via a shareable link. Participants can propose activities, vote, communicate in real-time, and track cost of committed activities. Plans move through defined states from planning → finalized → completed.

Plansly is inspired by platforms like Partiful, with additional emphasis on structured collaboration and payment coordination.

---

## 🧩 Core Concepts

Each **Plan** contains:

- Organizer and participants
- Activities and voting
- Deadline and status lifecycle
- Cost tracking and payment state
- Real-time chat
- Invitations and access control

### Plan Types

#### Trip
- Collaborative activity proposals
- Voting and selection

#### Event / Group Purchase
- Organizer-driven structure
- Simplified participation flow
- Shared cost tracking

---

## 🔑 Key Features

- Collaborative plan creation and management
- Shareable invitation links
- Real-time communication via WebSockets
- Activity proposals and voting
- Cost and payment tracking
- Image uploads via direct cloud storage
- Authenticated user sessions via OAuth

---

## 🏗️ Architecture Overview

Plansly follows a separated frontend/backend architecture.

The client communicates with a Flask backend API responsible for authentication, plan management, and real-time communication. External services handle identity management, data storage, and media storage.

### Design Goals

- Stateless backend using JWT authentication
- Real-time updates without polling
- Direct-to-cloud uploads for scalability
- Clear separation of identity, storage, and application logic

---

## ⚙️ Tech Stack

### Backend

- Flask (API server)
- Flask-JWT-Extended (JWT handling)
- Flask-SocketIO (real-time events)
- Flask-CORS (cross-origin configuration)
- MongoEngine + MongoDB (document data model)
- Authlib (Auth0 OAuth integration)
- boto3 (AWS S3 interaction)

### Infrastructure & Services

- Auth0 — authentication and identity management
- AWS S3 — media storage via pre-signed URLs
- MongoDB — primary database
- Render — deployment platform

### Development & Tooling

- python-dotenv (environment management)
- logging (centralized logging)
- redis (future caching layer)
- stripe (future payment integration)

---

## 🔐 Authentication & Storage

### Authentication Flow

1. Client initiates login
2. Backend redirects to Auth0
3. Auth0 returns OAuth callback
4. Backend validates identity and issues custom JWT
5. JWT stored as an HTTP-only cookie
6. Subsequent requests are authenticated automatically

This approach avoids exposing tokens to client-side JavaScript while maintaining stateless backend behavior.

### File Storage

User-uploaded images are not proxied through the backend.

1. Client requests an upload URL
2. Backend generates an S3 pre-signed URL
3. Client uploads directly to S3

This reduces server load and improves scalability.

---

## ⚡ Real-Time System

Plansly uses Socket.IO to synchronize state between participants.

- Users join a plan-specific room
- Messages and updates are broadcast to room members
- Active participants are tracked per plan
- Updates propagate without requiring page refreshes

Example events:

plan:join
plan:leave
plan:message:send
plan:update

---

## 🧭 Logging

Centralized logging is initialized in the app factory (`app/logger.py`) and shared across API routes and socket handlers.

---

## ⬇️ Local Development Setup

### 1) Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Configure environment variables
Create a .env file:
```bash
AUTH0_CLIENT_ID=
AUTH0_CLIENT_SECRET=
AUTH0_DOMAIN=
AUTH0_SECRET_KEY=

MONGO_URI=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION_NAME=
AWS_S3_BUCKET_NAME=

FRONTEND_URL=http://127.0.0.1:5173
BACKEND_URL=http://127.0.0.1:5001
ENV=development
LOG_LEVEL=INFO
```

### 4) Run server
```bash
python run.py
```


### 🚀 API Usage

Primary API groups:
```
/auth — authentication and session management

/plan — plan lifecycle and collaboration

/user — user data and participation
```

### 🧠 Future Improvements

```
- Redis caching layer for active plans and sessions

- Email notifications (invites, reminders) using SendGrid

- Stripe payment integration

- Test coverage

- Push-based plan updates via sockets

- Improved location/address handling
```

### 🫡 Feedback & Contributing

Feedback and contributions are welcome.