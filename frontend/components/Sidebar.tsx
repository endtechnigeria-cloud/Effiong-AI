'use client';

import { useState } from 'react';
import { User, BookOpen, Mic } from 'lucide-react';
import axios from 'axios';

export default function Sidebar() {
  const [contribName, setContribName] = useState('');
  const [dataType, setDataType] = useState('Historical Fact');
  const [heritageInput, setHeritageInput] = useState('');
  const [githubConsent, setGithubConsent] = useState(false);

  const handleSubmitHeritage = async () => {
    if (!heritageInput) return;
    try {
      await axios.post('http://localhost:8000/api/heritage', {
        contributor: contribName,
        type: dataType,
        record: heritageInput,
        consent: githubConsent
      });
      alert('Heritage record archived successfully!');
      setHeritageInput('');
    } catch (err) {
      alert('Failed to submit heritage record');
    }
  };

  return (
    <div className="p-6 h-full overflow-auto">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 bg-emerald-600 rounded-full flex items-center justify-center">
          🌍
        </div>
        <div>
          <h1 className="text-2xl font-bold">EFFIONG AI</h1>
          <p className="text-xs text-emerald-400">Sovereign Portal v5.0</p>
        </div>
      </div>

      <div className="space-y-8">
        {/* African Heritage Matrix */}
        <div>
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <BookOpen className="w-5 h-5" /> African Heritage Matrix
          </h2>
          <input
            type="text"
            placeholder="Contributor Identity"
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 mb-3"
            value={contribName}
            onChange={(e) => setContribName(e.target.value)}
          />
          <select
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 mb-3"
            value={dataType}
            onChange={(e) => setDataType(e.target.value)}
          >
            <option>Oral Story</option>
            <option>Linguistic Dialect</option>
            <option>Historical Fact</option>
            <option>Custom Tradition</option>
          </select>
          <textarea
            placeholder="Input Heritage Record Data..."
            className="w-full h-32 bg-gray-900 border border-gray-700 rounded-lg px-4 py-3"
            value={heritageInput}
            onChange={(e) => setHeritageInput(e.target.value)}
          />
          <button
            onClick={handleSubmitHeritage}
            className="w-full mt-4 bg-emerald-600 hover:bg-emerald-700 py-3 rounded-lg font-medium transition"
          >
            Submit to Archive
          </button>
        </div>

        {/* Voice & Settings */}
        <div>
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Mic className="w-5 h-5" /> Voice & Localization
          </h2>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={githubConsent} onChange={(e) => setGithubConsent(e.target.checked)} />
            Enable Anonymized GitHub Memory
          </label>
        </div>
      </div>
    </div>
  );
}
