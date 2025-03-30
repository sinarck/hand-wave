import React, { useState, useEffect, useRef } from "react";
import { Image, StyleSheet, Platform, View, Text } from "react-native";
import { Audio } from "expo-av";
import * as Speech from "expo-speech";

import { HelloWave } from "@/components/HelloWave";
import ParallaxScrollView from "@/components/ParallaxScrollView";
import { ThemedText } from "@/components/ThemedText";
import { ThemedView } from "@/components/ThemedView";

export default function HomeScreen() {
  const [translation, setTranslation] = useState("");
  const [lastMessage, setLastMessage] = useState("");
  const [connected, setConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);

  // Connect to WebSocket server
  useEffect(() => {
    // Replace with your computer's IP address
    const serverUrl = "ws://[replace here]:8765"; // Use your actual IP address

    // Create WebSocket connection
    ws.current = new WebSocket(serverUrl);

    // Connection opened
    ws.current.onopen = () => {
      console.log("Connected to ASL translation server");
      setConnected(true);
    };

    // Listen for messages
    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === "translation" && data.text) {
          setTranslation(data.text);
          setLastMessage(data.text);

          // Play audio of the translation
          Speech.speak(data.text, {
            language: "en",
            pitch: 1.0,
            rate: 0.9,
          });
        }
      } catch (error) {
        console.error("Error processing message:", error);
      }
    };

    // Handle errors
    ws.current.onerror = (error) => {
      console.error("WebSocket error:", error);
      setConnected(false);
    };

    // Connection closed
    ws.current.onclose = () => {
      console.log("Disconnected from server");
      setConnected(false);
    };

    // Cleanup on unmount
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  return (
    <ParallaxScrollView
      headerBackgroundColor={{ light: "#A1CEDC", dark: "#1D3D47" }}
      headerImage={
        <Image
          source={require("@/assets/images/partial-react-logo.png")}
          style={styles.reactLogo}
        />
      }
    >
      <ThemedView style={styles.titleContainer}>
        <ThemedText type="title">ASL Translator</ThemedText>
        <HelloWave />
      </ThemedView>

      {/* Connection status */}
      <ThemedView
        style={[
          styles.statusContainer,
          {
            backgroundColor: connected ? "#e0f7e0" : "#ffe0e0",
          },
        ]}
      >
        <ThemedText>
          Status:{" "}
          {connected ? "Connected to translation server" : "Disconnected"}
        </ThemedText>
      </ThemedView>

      {/* Translation display */}
      <ThemedView style={styles.translationContainer}>
        <ThemedText type="subtitle">Translation:</ThemedText>
        <ThemedView style={styles.messageBox}>
          <ThemedText type="defaultSemiBold" style={styles.translationText}>
            {translation || "Waiting for ASL translation..."}
          </ThemedText>
        </ThemedView>
      </ThemedView>

      {/* Recent translations */}
      <ThemedView style={styles.historyContainer}>
        <ThemedText type="subtitle">Last Message:</ThemedText>
        <ThemedView style={styles.messageBox}>
          <ThemedText>{lastMessage || "No messages yet"}</ThemedText>
        </ThemedView>
      </ThemedView>
    </ParallaxScrollView>
  );
}

const styles = StyleSheet.create({
  titleContainer: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  statusContainer: {
    padding: 10,
    borderRadius: 8,
    marginVertical: 10,
  },
  translationContainer: {
    gap: 8,
    marginBottom: 16,
  },
  historyContainer: {
    gap: 8,
    marginBottom: 16,
  },
  messageBox: {
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#ccc",
  },
  translationText: {
    fontSize: 18,
  },
  reactLogo: {
    height: 178,
    width: 290,
    bottom: 0,
    left: 0,
    position: "absolute",
  },
});

