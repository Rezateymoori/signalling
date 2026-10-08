# DirectChat Signaling - Cloudflare

این پروژه یک Signaling Server سبک برای DirectChat است.

## Deploy با Cloudflare

Repository را در GitHub قرار دهید و در Cloudflare Workers & Pages آن را متصل کنید.

تنظیمات:
- Build command: `npm install`
- Deploy command: `npx wrangler deploy`

پس از Deploy:
- تست سلامت: `/health`
- WebSocket: `/ws?room=global&user=USER_ID`

این سرویس برای Relay پیام‌های WebRTC مانند offer، answer و ICE در نظر گرفته شده است.
پیام‌های چت نباید در Signaling ذخیره شوند.
