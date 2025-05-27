import React, { useState } from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Typography,
  LinearProgress,
  Alert,
  Paper,
  Grid,
  Avatar,
  Stack,
  Divider,
  Chip
} from "@mui/material";
import Webcam from "react-webcam";
import axios from "axios";
import Swal from "sweetalert2";

const FaceSearch = () => {
  const [image, setImage] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const webcamRef = React.useRef(null);
  const fileInputRef = React.useRef(null);

  const captureImage = () => {
    const imageSrc = webcamRef.current.getScreenshot();
    setImage(imageSrc);
    setResults(null);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setImage(event.target.result);
        setResults(null);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSearch = async () => {
    if (!image) {
      Swal.fire({
        icon: "error",
        title: "Erreur",
        text: "Veuillez capturer ou uploader une image",
      });
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const blob = await fetch(image).then((res) => res.blob());
      const formData = new FormData();
      formData.append("image", blob, "search.jpg");

      const response = await axios.post(
        "http://localhost:8000/search_face/",
        formData
      );
      setResults(response.data);

      if (response.data.matched) {
        const topMatch = response.data.matches[0];
        Swal.fire({
          title: "Succès!",
          html: `<b>${topMatch.message}</b><br/>
                 ID Passager: <b>${topMatch.passenger_id}</b><br/>
                 Similarité: <b>${topMatch.percentage}%</b>`,
          icon: "success",
        });
      }
    } catch (err) {
      const errorMsg = err.response?.data?.message || err.message;
      setError(errorMsg);
      Swal.fire({
        icon: "error",
        title: "Erreur",
        text: errorMsg,
      });
    } finally {
      setLoading(false);
    }
  };

  const getPercentageColor = (percentage) => {
    if (percentage < 65) return "error";
    if (percentage < 80) return "warning";
    return "success";
  };

  const getMatchBadge = (index) => {
    const colors = ["success", "warning", "info"];
    const labels = ["1ère", "2ème", "3ème"];
    return (
      <Chip 
        label={`${labels[index]} place`}
        color={colors[index]}
        size="small"
        sx={{ ml: 1 }}
      />
    );
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mt: 2, borderRadius: 2 }}>
      <Typography variant="h6" gutterBottom sx={{ mb: 2, fontWeight: 600 }}>
        Reconnaissance Faciale
      </Typography>

      <Box sx={{ display: "flex", gap: 3, mb: 3 }}>
        {/* Colonne Webcam */}
        <Box sx={{ flex: 1 }}>
          <Webcam
            audio={false}
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            videoConstraints={{ facingMode: "user" }}
            style={{
              width: "100%",
              borderRadius: "8px",
              height: "300px",
              objectFit: "cover",
              boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
            }}
          />
          <Button
            variant="contained"
            fullWidth
            onClick={captureImage}
            sx={{
              mt: 2,
              py: 1,
              borderRadius: "6px",
              textTransform: "none",
              fontWeight: 500
            }}
          >
            Capturer l'image
          </Button>
        </Box>

        {/* Colonne Image */}
        <Box sx={{ flex: 1 }}>
          {image ? (
            <img
              src={image}
              alt="Captured"
              style={{
                width: "100%",
                height: "300px",
                objectFit: "cover",
                borderRadius: "8px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
              }}
            />
          ) : (
            <Box
              sx={{
                border: "2px dashed #ddd",
                borderRadius: "8px",
                height: "300px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                bgcolor: "#fafafa",
              }}
            >
              <Typography variant="body2" color="text.secondary">
                Aperçu de l'image capturée
              </Typography>
            </Box>
          )}
          <Button
            variant="outlined"
            fullWidth
            onClick={() => fileInputRef.current.click()}
            sx={{
              mt: 2,
              py: 1,
              borderRadius: "6px",
              textTransform: "none",
              fontWeight: 500
            }}
          >
            Uploader une image
          </Button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="image/*"
            style={{ display: "none" }}
          />
        </Box>
      </Box>

      <Button
        variant="contained"
        color="primary"
        fullWidth
        sx={{
          py: 1.5,
          borderRadius: "6px",
          textTransform: "none",
          fontWeight: 600,
          fontSize: "1rem",
          mb: 2,
          boxShadow: "none",
          "&:hover": {
            boxShadow: "none"
          }
        }}
        onClick={handleSearch}
        disabled={loading || !image}
      >
        {loading ? <CircularProgress size={24} color="inherit" /> : "Lancer la reconnaissance"}
      </Button>

      {error && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: "6px" }}>
          {error}
        </Alert>
      )}

      {results && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
            {results.message} (seuil: {results.threshold.toFixed(2)})
          </Typography>
          
          <Stack spacing={2}>
            {results.matches.map((match, index) => (
              <Card 
                key={index}
                sx={{
                  borderRadius: "8px",
                  boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
                  borderLeft: `4px solid ${
                    index === 0 ? "#4caf50" : 
                    index === 1 ? "#ff9800" : 
                    "#2196f3"
                  }`
                }}
              >
                <CardContent sx={{ p: 2 }}>
                  <Grid container spacing={2} alignItems="center">
                    {/* Photo de profil */}
                    <Grid item xs={3}>
                      <Box sx={{ 
                        display: "flex", 
                        flexDirection: "column",
                        alignItems: "center",
                        justifyContent: "center",
                        height: "100%"
                      }}>
                        <Avatar
                          src={match.user_image}
                          sx={{
                            width: 80,
                            height: 80,
                            mb: 1,
                            border: "2px solid #eee"
                          }}
                        />
                        <Typography variant="body2" color="text.secondary">
                          {match.user_id}
                        </Typography>
                      </Box>
                    </Grid>

                    {/* Détails de la correspondance */}
                    <Grid item xs={9}>
                      <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                          {match.message}
                        </Typography>
                        {getMatchBadge(index)}
                      </Box>

                      <Box sx={{ mb: 1 }}>
                        <Typography variant="body2">
                          <strong>ID Passager:</strong> {match.passenger_id}
                        </Typography>
                      </Box>

                      <Box sx={{ mb: 2 }}>
                        <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={match.percentage}
                            color={getPercentageColor(match.percentage)}
                            sx={{
                              height: 10,
                              flexGrow: 1,
                              borderRadius: "5px",
                              mr: 2
                            }}
                          />
                          <Typography
                            variant="body1"
                            sx={{ 
                              minWidth: "50px", 
                              fontWeight: "bold",
                              color: getPercentageColor(match.percentage) === "error" ? 
                                "#f44336" : 
                                getPercentageColor(match.percentage) === "warning" ? 
                                "#ff9800" : 
                                "#4caf50"
                            }}
                          >
                            {match.percentage}%
                          </Typography>
                        </Box>

                        <Grid container spacing={1}>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              <strong>Distance:</strong> {match.distance.toFixed(4)}
                            </Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              <strong>Seuil:</strong> {results.threshold.toFixed(2)}
                            </Typography>
                          </Grid>
                        </Grid>
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            ))}
          </Stack>
        </Box>
      )}
    </Paper>
  );
};

export default FaceSearch;