import React, { useEffect, useState } from 'react';
import api from '../api';

export default function Quote() {
  const [quote, setQuote] = useState('');

  useEffect(() => {
    loadQuote();
    const interval = setInterval(loadQuote, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadQuote = async () => {
    try {
      const data = await api.getQuote();
      setQuote(data.quote);
    } catch (error) {
      setQuote('Every line of code brings O4 Studio closer to reality.');
    }
  };

  return (
    <div className="card-glow h-full flex flex-col justify-center">
      <div className="text-primary text-xs font-heading tracking-[0.3em] mb-3">
        MOTIVATION
      </div>
      <blockquote className="font-body text-lg text-text leading-relaxed flex-1 flex items-center">
        <span className="text-primary text-4xl font-heading mr-2 opacity-50">"</span>
        {quote}
        <span className="text-primary text-4xl font-heading ml-2 opacity-50">"</span>
      </blockquote>
      <div className="mt-4 text-right">
        <span className="text-xs text-text-dim font-heading tracking-wider">- O4 STUDIO</span>
      </div>
    </div>
  );
}
