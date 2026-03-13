---
name: ninjaclawbot_control
description: Control NinjaClawBot through the official ninjaclawbot OpenClaw plugin tools.
---

# NinjaClawBot Control

Use the `ninjaclawbot_*` tools for all robot-related actions. Do not call raw driver CLIs, Python modules, or shell commands for robot hardware control.

## Core Rules

- When the plugin Always On lifecycle is enabled, the plugin itself now manages:
  - startup greeting
  - persistent `idle`
  - automatic `thinking` on incoming user messages
  - sleepy shutdown on gateway stop
- Use `ninjaclawbot_reply` for normal conversational replies instead of manually constructing expression chains.
- Use `ninjaclawbot_perform_expression` only when the user explicitly asks for a named expression or when a precise built-in expression is required.
- Use `ninjaclawbot_perform_movement` for saved robot motions.
- Use `ninjaclawbot_move_servos` only for deliberate low-level servo control tasks.
- If a robot tool fails or hardware seems unavailable, run `ninjaclawbot_health` before retrying.
- If an action looks unsafe or needs to stop immediately, use `ninjaclawbot_stop_all`.

## Reply Policy

- Greeting or warm welcome: use `reply_state: "greeting"`.
- Positive confirmation or simple acknowledgement: use `reply_state: "confirmation"`.
- Successful completion: use `reply_state: "success"`.
- Normal answer delivery: use `reply_state: "speaking"`.
- Thinking or deliberate pause: use `reply_state: "thinking"`.
- Clarifying question: use `reply_state: "asking_clarification"`.
- Cannot find an answer or uncertain: use `reply_state: "cannot_answer"` or `reply_state: "confusing"`.
- Warning or caution: use `reply_state: "warning"`.
- Failure or error reply: use `reply_state: "error"`.
- Sad or apologetic tone: use `reply_state: "sad"`.

## Idle Behavior

- When the Always On lifecycle is enabled, do not spam `ninjaclawbot_set_idle` after every normal reply because the plugin will return the robot to idle automatically.
- Use `ninjaclawbot_set_idle` only when you need to deliberately restore the robot to idle outside the normal lifecycle flow.
- After temporary reactions, prefer returning the robot to idle unless the current task clearly requires a different persistent state.

## Examples

- User says hello:
  call `ninjaclawbot_reply` with `text` set to the greeting reply and `reply_state: "greeting"`.
- You need clarification:
  call `ninjaclawbot_reply` with `reply_state: "asking_clarification"`.
- You cannot answer confidently:
  call `ninjaclawbot_reply` with `reply_state: "cannot_answer"`.
- A task completed successfully:
  call `ninjaclawbot_reply` with `reply_state: "success"`.
- The user explicitly asks for a saved movement:
  call `ninjaclawbot_perform_movement` with the saved movement name.

## Safety

- Do not move servos unless the user requested a physical robot action.
- Do not retry repeated movement or sound actions in a tight loop.
- If the robot behaves unexpectedly, use `ninjaclawbot_stop_all` and then `ninjaclawbot_health`.
