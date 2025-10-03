import express from "express";
import './backend/config/db.js';
import userRoutes from "./backend/routes/authRoutes.js";
import mediaRoutes from "./backend/routes/mediaRoutes.js"
import eventRoutes from "./backend/routes/eventRoutes.js"
import passport from "passport";
import pkg from "passport-jwt";

const { Strategy: JwtStrategy, ExtractJwt } = pkg;


const app = express();
const Port = 3000;

app.use(express.json());

app.use('/api', userRoutes);
app.use('/api', mediaRoutes);
app.use('/api', eventRoutes)


const opts = {
    jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
    secretOrKey: process.env.JWT_SECRET || "yoursecretkey" // put secret in .env
};

passport.use(
    new JwtStrategy(opts, (jwt_payload, done) => {
        try {
            // jwt_payload will contain user data you signed (ex: { id, email })
            // Here you could also fetch user from DB if needed
            return done(null, jwt_payload);
        } catch (err) {
            return done(err, false);
        }
    })
);

// Initialize Passport
app.use(passport.initialize());


app.listen(3000, () => {
    console.log(`Listening on port ${Port}`);
})