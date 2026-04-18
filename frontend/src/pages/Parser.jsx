import { useState } from "react";
import axios from "axios";

const Parser = () => {
  const [file, setFile] = useState(null);
  const [data, setData] = useState(null);

  const handleUpload = async () => {
    const formData = new FormData();
    formData.append("file", file);

    const res = await axios.post(
      "http://localhost:8000/parser/upload",
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );

    setData(res.data);
  };

  return (
    <div className="p-10 text-white">
      <h1 className="text-3xl mb-5">Resume Parser</h1>

      <input
        type="file"
        accept=".pdf"
        onChange={(e) => setFile(e.target.files[0])}
        className="mb-5"
      />

      <button 
        className="bg-blue-600 px-4 py-2 rounded" 
        onClick={handleUpload}
      >
        Parse Resume
      </button>

      {data && (
        <pre className="bg-black p-5 mt-5 rounded">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
};

export default Parser;
