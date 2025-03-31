import { useState, useEffect } from "react";
import axios from "axios";

const CameraStream = () => {
  const [imageSrc, setImageSrc] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [coordinates, setCoordinates] = useState(false);
  const [smileList, setSmileList] = useState([]);
  const [selectedSmile, setSelectedSmile] = useState("");
  const [smileDetected, setSmileDetected] = useState(false);
  const [smileImage, setSmileImage] = useState(null);

  useEffect(() => {
    let interval;
    if (isRunning) {
      interval = setInterval(async () => {
        // Check for a smile
        const response = await fetch("http://127.0.0.1:5000/detect-smile");
        const data = await response.json();
        setSmileDetected(data.smile_detected);
        setCoordinates(data.coordinates);

        setImageSrc(`http://127.0.0.1:5000/get-frame?t=${new Date().getTime()}`); // Prevent caching

      }, 1000);

    } else {
      setImageSrc(""); // Clear image when stopped
      setSmileDetected(false);
      setCoordinates('');
    }
    return () => clearInterval(interval);
  }, [isRunning]);

  const startCamera = async () => {
    const response = await fetch("http://127.0.0.1:5000/start-camera", { method: "POST" });
    if (response.ok) {
      setIsRunning(true);
    }
  };

  const stopCamera = async () => {
    await fetch("http://127.0.0.1:5000/stop-camera", { method: "POST" });
    setIsRunning(false);
    fetchSmiles();
  };

    // Fetch past smiles
    const fetchSmiles = async () => {
      const response = await axios.get("http://localhost:5000/get-smiles");
      setSmileList(response.data);
  };


  //   // Stop Camera
  //   const stopCamera = async () => {
  //     await axios.get("http://localhost:5000/stop-camera");
  //     setRunning(false);
  //     fetchSmiles();
  // };


      // Select past smile
      const handleSmileSelection = (event) => {
        const filename = event.target.value;
        setSelectedSmile(filename);
        //setSmileImage(`http://localhost:5000/get-image/${filename}`);
        setImageSrc(`http://localhost:5000/get-image/${filename}`); 
        //setImageSrc(`http://localhost:5000/get-image/${filename}`);
    };



  return (
    // <div style={{ display: "flex", height: "100vh" }}>

    // <div style={{ display: "flex", justifyContent: "space-between" }}>

    //   <div style={{ width: "50%" }}>


    <div style={{ display: "flex", height: "100vh" }}>
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", borderRight: "2px solid gray" }}>

        <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", borderRight: "2px solid gray" }}>
          {imageSrc ? <img src={imageSrc} alt="Camera Feed" width="90%" height="auto" /> : <p>No Camera Feed</p>}
        </div>

      </div>


          {/* <div style={{ width: "50%" }}> */}

          <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>

            <button onClick={startCamera} disabled={isRunning} style={{ margin: "10px", padding: "10px 20px" }}>Start Camera</button>
            <button onClick={stopCamera} disabled={!isRunning} style={{ margin: "10px", padding: "10px 20px" }}>Stop Camera</button>
            
            <h2 style={{ color: smileDetected ? "green" : "red" }}>
              {smileDetected ? "😊 Smile Detected!" : "😐 No Smile Detected"}
              {"  "}
              {coordinates}
            </h2>

                    Past Smiles{" "}<select onChange={handleSmileSelection}>
                        <option value="">Select a past smile</option>
                        {smileList.map((smile) => (
                            <option key={smile.timestamp} value={smile.filename}>
                                {smile.timestamp}
                            </option>
                        ))}
                    </select>

                    {smileImage && <img src={smileImage} alt="Smile" style={{ width: "100%" }} />}

          </div>
    </div>
  );
};

export default CameraStream;
