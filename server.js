import express from "express";
import session from "express-session"; // 1. Import express-session
import './backend/API/config/db.js';
import authRoutesAPI from "./backend/API/routes/authRoutesAPI.js";
import mediaRoutesAPI from "./backend/API/routes/mediaRoutesAPI.js"
import eventRoutesAPI from "./backend/API/routes/eventRoutesAPI.js";
import userRoutesAPI from "./backend/API/routes/userRoutesAPI.js";

const app = express();
const Port = 3000;

app.use(express.json());


app.use(session({
    
    secret: process.env.SESSION_SECRET || "your-super-secret-key-for-sessions",
    resave: false, 
    saveUninitialized: true, 
    cookie: {
        secure: process.env.NODE_ENV === "production", 
        maxAge: 1000 * 60 * 60 * 24 
    }
}));

// Your routes can now use req.session to store user data
app.use('/api', authRoutesAPI);
app.use('/api', mediaRoutesAPI);
app.use('/api', eventRoutesAPI);
app.use('/api', userRoutesAPI);

// --- All Passport and JWT related code has been removed ---

app.listen(3000, () => {
    console.log(`Listening on port ${Port}`);
});