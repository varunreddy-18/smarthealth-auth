export function decodeToken(token) {
  try {
    const payload = token.split(".")[1];

    const base64 = payload
      .replace(/-/g, "+")
      .replace(/_/g, "/");

    const decodedPayload = decodeURIComponent(
      window
        .atob(base64)
        .split("")
        .map((character) => {
          return (
            "%" +
            ("00" + character.charCodeAt(0).toString(16)).slice(-2)
          );
        })
        .join("")
    );

    return JSON.parse(decodedPayload);
  } catch {
    return null;
  }
}