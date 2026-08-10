db.createCollection("vehicle_telemetry", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["vehicle_id", "timestamp"],
      properties: {
        vehicle_id: {
          bsonType: "string",
          description: "Vehicle identifier (required)",
        },
        timestamp: {
          bsonType: "date",
          description: "UTC observation time (required)",
        },
        speed: { bsonType: ["double", "int", "long", "decimal", "null"] },
        odometer: { bsonType: ["double", "int", "long", "decimal", "null"] },
        soc: { bsonType: ["double", "int", "long", "decimal", "null"] },
        elevation: { bsonType: ["double", "int", "long", "decimal", "null"] },
        shift_state: { bsonType: ["string", "null"] },
      },
    },
  },
});

db.vehicle_telemetry.createIndex(
  { vehicle_id: 1, timestamp: 1 },
  { unique: true, name: "vehicle_timestamp_unique" },
);
