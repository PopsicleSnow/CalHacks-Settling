// Import the functions you need from the SDKs you need
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-analytics.js";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
    apiKey: "AIzaSyCn-lxVrX2t5rnMYxCXOMxfawhLoDG0b_Q",
    authDomain: "calhacks-a4f91.firebaseapp.com",
    projectId: "calhacks-a4f91",
    storageBucket: "calhacks-a4f91.appspot.com",
    messagingSenderId: "737816609018",
    appId: "1:737816609018:web:517d769e7f480611228943",
    measurementId: "G-RV7ZZKN60R"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
