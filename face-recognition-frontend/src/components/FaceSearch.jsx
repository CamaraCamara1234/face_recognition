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
} from "@mui/material";
import Webcam from "react-webcam";
import axios from "axios";
import Swal from "sweetalert2";

const FaceSearch = () => {
  const [image, setImage] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const webcamRef = React.useRef(null);
  const fileInputRef = React.useRef(null);

  const captureImage = () => {
    const imageSrc = webcamRef.current.getScreenshot();
    setImage(imageSrc);
    setResult(null);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setImage(event.target.result);
        setResult(null);
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
      setResult(response.data);

      if (response.data.success) {
        Swal.fire({
          title: "Succès!",
          text: `Utilisateur ${response.data.user_id} reconnu avec ${response.data.percentage}% de similarité`,
          icon: "success",
        });
      } else {
        Swal.fire({
          title: "Non reconnu",
          text: `La similarité (${response.data.percentage}%) est en dessous du seuil requis (65%)`,
          icon: "warning",
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

  return (
    <Paper elevation={3} sx={{ p: 2, mt: 2 }}>
      <Typography variant="h6" gutterBottom sx={{ mb: 1, fontSize: "1.1rem" }}>
        Reconnaissance Faciale
      </Typography>

      <Box sx={{ display: "flex", gap: 2, mb: 2 }}>
        {/* Colonne Webcam */}
        <Box sx={{ flex: 1 }}>
          <Webcam
            audio={false}
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            videoConstraints={{ facingMode: "user" }}
            style={{
              width: "100%",
              borderRadius: "4px",
              height: "350px",
              objectFit: "cover",
            }}
          />
          <Button
            variant="contained"
            fullWidth
            onClick={captureImage}
            sx={{
              mt: 1,
              py: 0.5,
              fontSize: "0.75rem",
            }}
            size="small"
          >
            Capturer
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
                height: "350px",
                objectFit: "cover",
                borderRadius: "4px",
              }}
            />
          ) : (
            <Box
              sx={{
                border: "1px dashed #ccc",
                borderRadius: "4px",
                height: "350px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                bgcolor: "#f5f5f5",
              }}
            >
              <Typography variant="caption" color="text.secondary">
                Aperçu
              </Typography>
            </Box>
          )}
          <Button
            variant="outlined"
            fullWidth
            onClick={() => fileInputRef.current.click()}
            sx={{
              mt: 1,
              py: 0.5,
              fontSize: "0.75rem",
            }}
            size="small"
          >
            Uploader
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
          py: 0.6,
          fontSize: "0.75rem",
          mb: 1,
        }}
        onClick={handleSearch}
        disabled={loading || !image}
        size="small"
      >
        {loading ? <CircularProgress size={16} /> : "Rechercher"}
      </Button>

      {error && (
        <Alert severity="error" sx={{ py: 0.5, fontSize: "0.75rem" }}>
          {error}
        </Alert>
      )}

      {result && (
        <Card
          sx={{
            mt: 1,
            borderRadius: "4px",
            width: "100%",
            maxWidth: "800px",
            marginLeft: "auto",
            marginRight: "auto",
          }}
        >
          <CardContent sx={{ p: 1 }}>
            <Grid container spacing={2}>
              {/* Colonne Image */}
              {result.user_image && (
                <Grid item xs={4}>
                  {" "}
                  {/* Réduit à 4 colonnes sur 12 pour l'image */}
                  <Box
                    sx={{
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      justifyContent: "center",
                      height: "100%",
                    }}
                  >
                    <Avatar
                      src={result.user_image}
                      sx={{
                        width: 100,
                        height: 100,
                        mb: 1,
                      }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      Photo de référence
                    </Typography>
                  </Box>
                </Grid>
              )}

              {/* Colonne Résultats - Prend tout l'espace restant */}
              <Grid item xs={result.user_image ? 8 : 12}>
                {" "}
                {/* 8 colonnes quand il y a une image, 12 sinon */}
                <Box
                  sx={{
                    display: "flex",
                    flexDirection: "column",
                    height: "100%",
                    justifyContent:
                      "space-between" /* Répartit l'espace verticalement */,
                  }}
                >
                  <Typography
                    variant="subtitle2"
                    sx={{ fontWeight: 600, mb: 1 }}
                  >
                    Résultats
                  </Typography>

                  {result.success ? (
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        <strong>{result.user_id}</strong>
                      </Typography>

                      <Box sx={{ mb: 2 }}>
                        <Box
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            gap: 1,
                            mb: 1,
                          }}
                        >
                          <LinearProgress
                            variant="determinate"
                            value={result.percentage}
                            color={getPercentageColor(result.percentage)}
                            sx={{
                              height: 10 /* Un peu plus épais */,
                              flexGrow: 1,
                              borderRadius: "3px",
                            }}
                          />
                          <Typography
                            variant="body1"
                            sx={{ minWidth: "40px", fontWeight: "bold" }}
                          >
                            {result.percentage}%
                          </Typography>
                        </Box>

                        <Grid container spacing={1}>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              Distance: {result.distance.toFixed(2)}
                            </Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              Seuil: {result.threshold.toFixed(2)}
                            </Typography>
                          </Grid>
                        </Grid>
                      </Box>
                    </Box>
                  ) : (
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="body2" color="error" sx={{ mb: 1 }}>
                        Non reconnu
                      </Typography>
                      {result.percentage > 0 && (
                        <Box>
                          <Box
                            sx={{
                              display: "flex",
                              alignItems: "center",
                              gap: 1,
                              mb: 1,
                            }}
                          >
                            <LinearProgress
                              variant="determinate"
                              value={result.percentage}
                              color={getPercentageColor(result.percentage)}
                              sx={{
                                height: 10,
                                flexGrow: 1,
                                borderRadius: "3px",
                              }}
                            />
                            <Typography
                              variant="body1"
                              sx={{ minWidth: "40px", fontWeight: "bold" }}
                            >
                              {result.percentage}%
                            </Typography>
                          </Box>
                          <Typography variant="body2" color="text.secondary">
                            (seuil minimum à 65%)
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  )}
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}
    </Paper>
  );
};

export default FaceSearch;
