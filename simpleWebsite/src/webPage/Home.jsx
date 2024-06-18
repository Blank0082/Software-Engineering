import React, {useEffect, useState} from 'react';
import Navbar from "../components/Navbar";
import '../css/Home.css';

function Home() {
    const [text, setText] = useState('');
    const [isDeleting, setIsDeleting] = useState(false);
    const [loopNum, setLoopNum] = useState(0);
    const [typingSpeed, setTypingSpeed] = useState(150);

    useEffect(() => {
        const phrases = ["歡迎使用", "手寫作文辨識系統", " "];
        const handleType = () => {
            const currentPhrase = phrases[loopNum % phrases.length];
            setText(isDeleting
                ? currentPhrase.substring(0, text.length - 1)
                : currentPhrase.substring(0, text.length + 1)
            );

            setTypingSpeed(isDeleting ? 75 : 150);

            if (!isDeleting && text === currentPhrase) {
                setTimeout(() => setIsDeleting(true), 1000);
            } else if (isDeleting && text === '') {
                setIsDeleting(false);
                setLoopNum(loopNum + 1);
            }
        };

        const timer = setTimeout(handleType, typingSpeed);

        return () => clearTimeout(timer);
    }, [text, isDeleting, loopNum, typingSpeed]);

    return (
        <div className="home">
            <div className="background_container"></div>
            <div className="title">
                <Navbar/>
                <p className="first_p">{text}<span className="cursor">{isDeleting ? '_' : ''}</span></p>
            </div>
        </div>
    );
}

export default Home;