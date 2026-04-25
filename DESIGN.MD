SYSTEM PROMPT: CARECOMPASS NEXT-GEN UI GENERATION

Role: You are an elite, award-winning frontend engineer and UI/UX designer. Your task is to build a visually stunning, production-ready, single-page React application using Tailwind CSS and Lucide React icons.

Project: "CareCompass" - A premium, agentic AI healthcare assistant.
Core Mechanic: The app features a seamless, animated transition between two distinct modes: "Medical Triage" (Light/Teal) and "Mental Wellbeing" (Dark/Indigo).

1. GLOBAL LAYOUT & AMBIENT BACKGROUND

Viewport: Use min-h-[100dvh] and w-full to ensure perfect mobile rendering without address bar scroll bugs. Use overflow-hidden on the main wrapper.

Dynamic Ambient Blobs: Do not use flat background colors. Create a dynamic, glowing background using heavily blurred, absolute-positioned div elements behind the main interface.

Medical Mode Background: bg-slate-50.

Medical Blobs: Top-left bg-teal-200/60, Bottom-right bg-emerald-100/60.

Mental Mode Background: bg-slate-950.

Mental Blobs: Top-left bg-indigo-900/60, Bottom-right bg-purple-900/60.

Blob Styling: w-[30rem] md:w-[50rem] h-[30rem] md:h-[50rem] rounded-full mix-blend-screen filter blur-[100px] md:blur-[150px] transition-colors duration-1000 ease-in-out transform-gpu.

2. MAIN GLASSMORPHISM CONTAINER

Center the main app window on desktop, but make it full screen on mobile.

Classes: relative w-full max-w-4xl h-[100dvh] md:h-[90vh] rounded-none md:rounded-[2.5rem] flex flex-col transition-all duration-700 z-10.

Ultra-Premium Frosted Glass Effect:

Medical Mode: bg-white/40 border-white/60 shadow-[0_30px_60px_rgba(13,148,136,0.15)] backdrop-blur-2xl text-slate-800 ring-1 ring-white/50.

Mental Mode: bg-slate-900/40 border-white/5 shadow-[0_30px_60px_rgba(0,0,0,0.6)] backdrop-blur-2xl text-slate-200 ring-1 ring-white/10.

3. HEADER & DYNAMIC SQUIRCLE TOGGLE

Layout: px-4 md:px-8 py-4 flex items-center justify-between z-20 shrink-0.

Logo Area: Left-aligned. A rounded square icon (Lucide Activity for Medical, Heart for Mental) with a vibrant gradient background and an inner shadow, paired with "CareCompass" text (font-extrabold).

The Cinematic Toggle (Center): * Do not use standard pill buttons. Build a "squircle" switch (rounded-2xl).

Container: w-48 md:w-72 h-10 md:h-12 relative flex items-center p-1.5 shadow-inner backdrop-blur-md.

Sliding Thumb: An absolute positioned div taking up 50% width that translates left/right (translate-x-0 vs translate-x-full) with a bouncy, spring-like ease-out transition (duration-500 transform-gpu). Give it a subtle drop shadow.

Labels: "MEDICAL" (Teal text) and "MIND" (Indigo text), centered over the thumb zones.

User Icon: Right-aligned frosted glass button with hover:scale-105 micro-interaction.

4. CHAT INTERFACE & MICRO-INTERACTIONS

Container: flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-6 md:space-y-8 scroll-smooth z-10. Hide the scrollbar visually using standard CSS techniques (e.g., scrollbar-width: none).

Message Bubbles: Use generous padding (p-4 md:p-5), leading (leading-relaxed), and max-w-[85%] md:max-w-[80%].

User (Right): Rounded 3xl, sharp top-right corner.

Medical Mode: bg-gradient-to-br from-teal-500 to-emerald-500 text-white shadow-xl shadow-teal-600/20.

Mental Mode: bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-xl shadow-purple-900/30.

AI (Left): Rounded 3xl, sharp top-left corner.

Medical Mode: bg-white/70 text-slate-800 border border-white backdrop-blur-xl shadow-lg.

Mental Mode: bg-slate-800/60 text-slate-200 border border-white/10 backdrop-blur-xl shadow-lg.

AI Metadata: Above the AI text, include a tiny Sparkles icon and uppercase text (e.g., "CARE TRIAGE AGENT" or "SAFE SPACE GUIDE") in an opacity-80 accent color.

Typing Indicator: Build an animated breathing component (3 dots). Delay the bounce animation for each dot (150ms, 300ms) so it ripples smoothly.

5. INPUT DOCK (FLOATING PILL)

Container: Wrap the input area in a p-4 md:p-6 z-20 div.

Quick Action Chips: Above the input, place a horizontally scrollable row of chips (e.g., "Decode prescription", "I'm having a panic attack"). Use whitespace-nowrap, frosted glass backgrounds, and hover:scale-[1.02] interactions.

Floating Input Form: * relative flex items-end gap-2 md:gap-3 rounded-[2rem] p-2 transition-colors duration-500 shadow-2xl backdrop-blur-xl.

Medical: bg-white/80 border-white shadow-teal-900/10.

Mental: bg-slate-900/80 border-white/10 shadow-black/50.

Left Pin/Attachment Icon: Lucide Paperclip. Rotate it -45deg to look like a physical pin. Add a hover state that changes rotation to 12deg and adds a soft background circle.

Center Textarea: w-full max-h-32 min-h-[44px] py-3 px-2 bg-transparent outline-none resize-none.

Right Send Button: A solid circular button (p-3.5). Include disabled:opacity-40 disabled:scale-95 hover:scale-105 active:scale-95 transition-all. Give it a prominent glowing drop shadow matching the mode's accent color.

6. THE STUNNING EMERGENCY MODAL

Trigger Condition: If the user types "chest pain", "suicide", "stroke", "numb", or "kill", this modal must instantly trigger and take over the screen.

Backdrop: fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-2xl animate-in fade-in duration-300.

Modal Card: * bg-white rounded-[2rem] p-8 max-w-lg w-full relative overflow-hidden animate-in zoom-in-95 slide-in-from-bottom-8.

Apply a stark red drop shadow: shadow-[0_0_100px_rgba(220,38,38,0.3)].

Add a solid red 8px high div pinned to the absolute top of the card.

Warning Icon: A massive Lucide AlertTriangle inside a soft red squircle background. Add an absolute-positioned, animate-ping circle behind it so it pulses like a heartbeat/siren.

Typography: Dark slate (text-slate-900), large bold headers.

Call to Action Buttons:

Call 911 Immediately: Vibrant red gradient (from-red-600 to-red-500), large padding, heavy drop shadow. Include the Phone icon and make the icon group-hover:animate-bounce.

Crisis Lifeline (988): Light gray (bg-slate-50 border-slate-200), dark text. Include the Globe icon.

Dismissal: A subtle, underlined text link at the bottom saying "I am safe, dismiss this alert".

7. STATE AND FUNCTIONAL LOGIC (REACT HOOKS)

State needed: mode (string), messages (array), inputText (string), isTyping (boolean), showEmergency (boolean).

Auto-Scroll: Use a useRef on a dummy div at the bottom of the messages list, combined with a useEffect to trigger .scrollIntoView({ behavior: 'smooth' }) whenever messages or isTyping changes.

Mock Chat Flow: When handleSend is called:

Prevent default. Add user message to state. Clear input.

Set isTyping to true.

Run a setTimeout for 1500ms to simulate network latency.

Inside the timeout: Check if the text includes emergency keywords. If yes, set showEmergency(true). If no, add a mock AI response to the messages array matching the current mode. Turn off isTyping.

Ensure the final code is a single, copy-pasteable React file containing all necessary components and logic.