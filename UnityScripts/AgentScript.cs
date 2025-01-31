using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System;
using System.Net;
using System.Net.Sockets;
using System.Threading;

public class AgentScript : MonoBehaviour
{

    private Socket socket;

    // Due to weird scaling issues I hard coded the unity equivalent of each coordinate from the grid
    float[] xPositions = {0.166f, 0.465f, 0.818f, 1.123f, 1.453f, 1.765f, 2.076f, 2.412f, 2.725f, 3.057f, 3.378f, 3.71f, 4.031f, 4.352f, 4.678f, 5.016f, 5.33f, 5.608f, 5.945f, 6.332f, 6.639f, 6.957f, 7.262f, 7.569f, 7.908f, 8.244f, 8.561f, 8.863f, 9.213f, 9.536f, 9.841f};

    private void Start()
    {
        
        // Move to the starting spot
        Vector3 newPosition = new Vector3(xPositions[6], 0, -xPositions[0]);
        transform.localPosition = newPosition;

        const int BUFFER_SIZE = 4096;
        byte[] readBuff = new byte[BUFFER_SIZE];
        String str;
        int count;

        // Connect to the socket
        socket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
        socket.Connect("127.0.0.1", 1101);
        Debug.Log("Connected to Socket!");

        count = socket.Receive(readBuff);
        str = System.Text.Encoding.UTF8.GetString(readBuff, 0, count);

        // Make sure the server knows we're ready
        if (str == "R?") {
            str = "R";
            byte[] bytes = System.Text.Encoding.Default.GetBytes(str);
            socket.Send(bytes);
            Debug.Log("Ready");

            // Start moving
            StartCoroutine(Move());
        }

    }

    private IEnumerator Move()
    {
        const int BUFFER_SIZE = 4096;
        byte[] readBuff = new byte[BUFFER_SIZE];
        int count;
        String str = "";
        
        // Keep moving until we receive the end signal
        while (str != "E") {
            count = socket.Receive(readBuff);
            str = System.Text.Encoding.UTF8.GetString(readBuff, 0, count);

            string[] parts = str.Split(" ");

            // According to the protocol this is a movement
            if (parts[0] == "M") {
                int x = Int32.Parse(parts[1]);
                int y = Int32.Parse(parts[2]);

                Vector3 newPosition = new Vector3(xPositions[x], 0, -xPositions[y]);
                transform.localPosition = newPosition;
            }

            // Wait until next frame to check for the next instruction
            yield return null;
        }
    }

    private void OnDestroy() {
        // Close the connection at the end
        socket.Close();
    }

}
