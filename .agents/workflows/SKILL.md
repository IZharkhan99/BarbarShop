---
description: Development rules and quality standards for the Barber Shop Management App
---

# Skill Requirements

## Project Overview
This project is a **Barber Shop Management App**. The goal is to make the application **fully responsive, production-ready, and optimized for both desktop and mobile devices**, while ensuring **complete compatibility with Electron**.

---

## 1. Important Development Rule
- **Do not break the existing logic or working code.**
- Improvements are allowed, but the **current flow of the barber shop application must remain the same**.
- Do not change the **business logic, data flow, or functionality** unless absolutely necessary to fix a bug.
- Focus on **enhancing UI, responsiveness, and stability** without modifying how the app works.

---

## 2. Responsive Design
- The application must be **fully responsive** across all screen sizes.
- It should work perfectly on:
  - Desktop screens
  - Tablets
  - Small mobile screens
- UI elements should automatically adjust using **responsive layouts**.
- Avoid horizontal scrolling on mobile devices.
- Maintain proper spacing, alignment, and readability.

---

## 3. Electron Compatibility
The app will run inside **Electron**, so every feature must work correctly within the Electron environment.

Ensure the following components work perfectly:
- Modals
- Text inputs
- Buttons
- Navigation
- Sidebar interactions
- Forms
- Dialogs
- File handling (if used)

No UI elements should break or become unresponsive in Electron.

---

## 4. Premium UI / UX
The application should feel **modern and premium**.

Requirements:
- Clean layout
- Smooth interactions
- Consistent colors and spacing
- Proper typography
- Professional dashboard design
- Clear visual hierarchy
- User-friendly navigation

---

## 5. Dashboard & Data Handling
When displaying data in dashboards or lists:

- If the data becomes **large**, the UI must handle it properly using:
  - Scrollable containers
  - Pagination
  - "Load More" functionality
- Tables and lists must remain **smooth and readable** even with large datasets.

---

## 6. Date Filter Functionality
Date filtering must work **correctly and consistently** across the app.

Requirements:
- When a date filter is applied:
  - All related data must update accordingly.
  - Dashboard cards (Total Revenue, Total Jobs, etc.) must also update.
- No component should ignore the applied filter.

---

## 7. Performance & Stability
- The application must remain **fast and stable**.
- Avoid unnecessary re-renders or heavy UI operations.
- Ensure smooth performance inside Electron.

---

## 8. Completion Standard
The application should feel **fully complete and production-ready**.

That includes:
- Working navigation
- Functional dashboards
- Responsive UI
- Stable Electron behavior
- Proper handling of large data
- Smooth user experience

---

## 9. Mobile Access via Exposed IP
- In the **Settings section**, the exposed IP feature must work properly.
- When the IP is exposed, the application should be **accessible from mobile devices on the same network**.
- All features must function correctly when accessed from mobile through the exposed IP.
- Ensure the UI remains **fully responsive and usable on mobile browsers**.

No partially implemented features should remain.
