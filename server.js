import express from "express";
import './backend/config/db.js';
import userRoutes from "./backend/routes/authRoutes.js";

const app = express();
const Port = 3000;

app.use(express.json());

app.use('/api', userRoutes);


app.listen(3000, () => {
    console.log(`Listening on port ${Port}`);
})