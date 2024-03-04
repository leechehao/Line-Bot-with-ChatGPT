# Line Bot with ChatGPT
開發基於 RAG (Retrieval-Augmented Generation) 架構的聊天機器人，結合資訊檢索與自然語言生成技術，實現準確回答與豐富對話內容。透過即時檢索相關訊息與生成回應，提升回答的相關性與品質。後端服務採用 Flask 框架，主要負責建置與 Line Bot 互動所需的 webhook 以及管理 API 呼叫流程，以便 Line 平台上的聊天機器人能夠順利接收與回應用戶訊息。此外，透過使用 ngrok 將本地開發的後端服務安全地對外公開，確保穩定連接。同時，採用 Redis 緩存對話記錄，增強性能與回應速度，為用戶帶來更流暢的互動體驗。

## :rocket: Quick Start
[教學 Blog](https://hackmd.io/@6j0OMC7UQbGqQLfUg9pauA/rJYqWy1d3)