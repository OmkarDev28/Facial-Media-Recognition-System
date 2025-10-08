import express from "express";
import passport from "passport";
import multer from "multer";
import fs from "fs";
import path from "path";
import pool from "../config/db.js";

const router = express.Router();

// Multer storage config (dynamic folder based on event_id)
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    const { event_id } = req.body;
    const uploadPath = path.join("uploads", `event_${event_id}`);

    // Create folder if it doesn't exist
    if (!fs.existsSync(uploadPath)) {
      fs.mkdirSync(uploadPath, { recursive: true });
    }

    cb(null, uploadPath);
  },
  filename: function (req, file, cb) {
    const uniqueName = Date.now() + "-" + file.originalname;
    cb(null, uniqueName);
  },
});

const upload = multer({ storage });

// Media Upload API (Protected with JWT)
router.post(
  "/media/upload",
  
  upload.single("file"),
  async (req, res) => {
    try {
      const userId = 5;
      const { event_id, description, file_type } = req.body;

      if (!req.file) {
        return res.status(400).json({ error: "No file uploaded" });
      }

      const fileUrl = `/uploads/event_${event_id}/${req.file.filename}`;

      // Insert into DB
      const result = await pool.query(
        "INSERT INTO media (user_id, event_id, file_url, file_type, description) VALUES ($1, $2, $3, $4, $5) RETURNING *",
        [userId, event_id, fileUrl, file_type, description]
      );

      res.status(201).json({
        message: "Media uploaded successfully",
        media: result.rows[0],
      });
    } catch (err) {
      console.error("Upload error:", err);
      res.status(500).json({ error: "Server error" });
    }
  }
);

export default router;
