import React from 'react';
import './SuggestedQuestions.css';

function SuggestedQuestions({ questions, onQuestionClick }) {
  return (
    <div className="suggested-questions">
      {questions.map((question, index) => (
        <button 
          key={index} 
          className="question-button"
          onClick={() => onQuestionClick(question)}
        >
          {question}
        </button>
      ))}
    </div>
  );
}

export default SuggestedQuestions; 