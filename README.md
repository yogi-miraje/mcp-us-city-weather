# Weather MCP Server

This repository contains a weather information service built using the MCP (Model-Completion-Protocol) framework. The service provides weather forecasts for any city by leveraging the National Weather Service (NWS) API.

## Features

- Geocode city names to latitude/longitude coordinates
- Fetch weather data from the National Weather Service API
- Get detailed weather forecasts including temperature, conditions, and wind information
- Modular design with separate tools for each step of the process

## Available MCP Tool

- `get_weather`: Get complete weather information for a city

## Usage

### Test the MCP Server Locally

To test the MCP server locally, use:

```
mcp dev weather.py
```

### Use with Claude Desktop

To use this weather server with Claude Desktop, add the following configuration to your Claude Desktop config:

```json
{
  "mcpServers": {
    "my_python_server": {
      "command": "/Users/<user_name>/.local/bin/uv",
      "args": [
        "--directory",
        "/Users/<user_name>/<git_repository_path>",
        "run",
        "weather.py"
      ]
    }
  }
}
```

Make sure to replace the directories with your own path: `</Users/user_name/Your_directory>`

## Example

Once configured, you can ask Claude questions like:
- "What's the weather in San Francisco?"
- "How's the weather in New York City?"
- "Get me the weather forecast for Chicago"

Claude will use the MCP server to fetch and display the weather information.
