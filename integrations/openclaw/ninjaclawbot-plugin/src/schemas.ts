export const replyStates = [
  "asking_clarification",
  "cannot_answer",
  "confirmation",
  "confusing",
  "curious",
  "error",
  "greeting",
  "listening",
  "sad",
  "sleepy",
  "speaking",
  "success",
  "thinking",
  "warning",
] as const;

export const speedModes = ["S", "M", "F"] as const;

export const replySchema = {
  type: "object",
  additionalProperties: false,
  properties: {
    text: { type: "string", minLength: 1 },
    reply_state: { type: "string", enum: [...replyStates] },
    display_text: { type: "string" },
    duration: { type: "number", minimum: 0 },
    language: { type: "string" },
    font_size: { type: "integer", minimum: 1 },
  },
  required: ["text", "reply_state"],
} as const;

export const nameSchema = {
  type: "object",
  additionalProperties: false,
  properties: {
    name: { type: "string", minLength: 1 },
  },
  required: ["name"],
} as const;

export const moveServosSchema = {
  type: "object",
  additionalProperties: false,
  properties: {
    targets: {
      type: "object",
      minProperties: 1,
      additionalProperties: { type: "number" },
    },
    speed_mode: { type: "string", enum: [...speedModes] },
    per_servo_speeds: {
      type: "object",
      additionalProperties: { type: "string", enum: [...speedModes] },
    },
    easing: { type: "string" },
    force: { type: "boolean" },
  },
  required: ["targets"],
} as const;

export const capturePhotoSchema = {
  type: "object",
  additionalProperties: false,
  properties: {
    output_path: { type: "string", minLength: 1 },
  },
} as const;

export const recognizeFacesSchema = {
  type: "object",
  additionalProperties: false,
  properties: {
    image_path: { type: "string", minLength: 1 },
  },
} as const;

export const enrollPendingFaceSchema = {
  type: "object",
  additionalProperties: false,
  properties: {
    recognition_id: { type: "string", minLength: 1 },
    face_id: { type: "string", minLength: 1 },
    name: { type: "string", minLength: 1 },
  },
  required: ["recognition_id", "face_id", "name"],
} as const;

export const noArgsSchema = {
  type: "object",
  additionalProperties: false,
  properties: {},
} as const;
