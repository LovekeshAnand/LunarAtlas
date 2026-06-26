import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { apiService } from '../services/apiService';

// Styling constants matching DocsPage and modern professional research layout
const CODE = 'bg-neutral-100 dark:bg-[#18181d] border border-neutral-200 dark:border-neutral-800 px-[6px] py-[2px] font-mono text-[11.5px] text-neutral-800 dark:text-[#d0d0d0] tracking-[0.1px] rounded-sm';
const CODEBLK = 'bg-neutral-50 dark:bg-[#0f0f12] border border-neutral-200 dark:border-neutral-800 px-5 py-4 my-3 font-mono text-[12px] text-neutral-800 dark:text-[#c0c0c0] overflow-x-auto leading-[1.6] whitespace-pre rounded-md';
const TABLE = 'w-full border-collapse my-3 text-[12px] text-left';
const TH = 'text-[9px] font-bold tracking-[1.5px] text-neutral-800 dark:text-neutral-300 uppercase px-4 py-2.5 border-b border-neutral-200 dark:border-neutral-800 bg-neutral-50/50 dark:bg-[#141414]';

interface EndpointDoc {
  id: string;
  method: 'GET' | 'POST';
  path: string;
  description: string;
  params: { name: string; type: string; req: boolean | string; def?: string; desc: string }[];
  curlExample: string;
  sampleResponse: any;
}

export default function DeveloperApiPage() {
  const [activeSnippetTab, setActiveSnippetTab] = useState<'curl' | 'python' | 'node' | 'go' | 'r'>('curl');
  const [expandedEndpoint, setExpandedEndpoint] = useState<string | null>('spectra_bulk');
  const [customKey, setCustomKey] = useState('');

  // Authoritative expected responses based on real database tables
  const endpointDocs: EndpointDoc[] = [
    {
      id: 'missions',
      method: 'GET',
      path: '/public/missions',
      description: 'Retrieve the active catalog list of planetary space exploration missions.',
      params: [
        { name: 'limit', type: 'Integer', req: false, def: '10', desc: 'Pagination size limit (1 - 100)' },
        { name: 'offset', type: 'Integer', req: false, def: '0', desc: 'Pagination index offset' }
      ],
      curlExample: 'curl -H "X-API-Key: YOUR_API_KEY" "http://localhost:8000/api/v1/public/missions?limit=5"',
      sampleResponse: {
        meta: {
          agency: "ISRO",
          data_standard: "PDS4",
          licensing: "ISRO Open Data Sharing Policy (ISDA)",
          api_version: "1.0.0",
          rate_limit_limit: 1000,
          rate_limit_remaining: 999,
          timestamp: "2026-06-14T12:00:00.000Z"
        },
        results: [
          {
            mission_id: "1",
            mission_code: "CH3",
            mission_name: "Chandrayaan-3",
            organization: "ISRO",
            launch_date: "2023-07-14T09:05:00Z",
            target_body: "Moon",
            description: "Third Indian lunar exploration mission under ISRO's Chandrayaan program."
          }
        ],
        links: {
          self: "/api/v1/public/missions?limit=5&offset=0",
          next: null,
          prev: null
        }
      }
    },
    {
      id: 'missions_detail',
      method: 'GET',
      path: '/public/missions/{code}',
      description: 'Retrieve detailed metadata and descriptions for a specific mission by its short code.',
      params: [
        { name: 'code', type: 'String (Path)', req: true, desc: 'Target mission code, e.g., CH3 (case-insensitive)' }
      ],
      curlExample: 'curl -H "X-API-Key: YOUR_API_KEY" "http://localhost:8000/api/v1/public/missions/CH3"',
      sampleResponse: {
        meta: {
          agency: "ISRO",
          data_standard: "PDS4",
          licensing: "ISRO Open Data Sharing Policy (ISDA)",
          api_version: "1.0.0",
          rate_limit_limit: 1000,
          rate_limit_remaining: 998,
          timestamp: "2026-06-14T12:01:00.000Z"
        },
        results: {
          mission_id: "1",
          mission_code: "CH3",
          mission_name: "Chandrayaan-3",
          organization: "ISRO",
          launch_date: "2023-07-14T09:05:00Z",
          target_body: "Moon",
          description: "Third Indian lunar exploration mission under ISRO's Chandrayaan program."
        },
        links: {
          self: "/api/v1/public/missions/CH3",
          parent: "/api/v1/public/missions"
        }
      }
    },
    {
      id: 'instruments',
      method: 'GET',
      path: '/public/instruments',
      description: 'Query list of scientific payload sensor packages cataloged in the system.',
      params: [
        { name: 'mission_code', type: 'String', req: false, desc: 'Filter by mission short code, e.g., CH3' }
      ],
      curlExample: 'curl -H "X-API-Key: YOUR_API_KEY" "http://localhost:8000/api/v1/public/instruments?mission_code=CH3"',
      sampleResponse: {
        meta: {
          agency: "ISRO",
          data_standard: "PDS4",
          licensing: "ISRO Open Data Sharing Policy (ISDA)",
          api_version: "1.0.0",
          rate_limit_limit: 1000,
          rate_limit_remaining: 997,
          timestamp: "2026-06-14T12:02:00.000Z"
        },
        results: [
          {
            instrument_id: "1",
            mission_id: 1,
            instrument_code: "LIBS",
            instrument_name: "Laser Induced Breakdown Spectroscope",
            instrument_type: "Spectrometer",
            description: "Qualitative and quantitative elemental analysis of lunar soil at the landing site."
          }
        ],
        links: {
          self: "/api/v1/public/instruments?mission_code=CH3"
        }
      }
    },
    {
      id: 'observations',
      method: 'GET',
      path: '/public/observations',
      description: 'Query PDS observational collections conforming strictly to logical metadata index archives.',
      params: [
        { name: 'mission', type: 'String', req: 'Recommended', desc: 'Mission filter code (e.g. CH3)' },
        { name: 'instrument', type: 'String', req: 'Recommended', desc: 'Instrument filter code (e.g. LIBS)' },
        { name: 'target_name', type: 'String', req: 'Optional', desc: 'Filter by target celestial body, e.g., Moon' },
        { name: 'date', type: 'String (YYYY-MM-DD)', req: 'Recommended', desc: 'Filter by observation capture date' },
        { name: 'limit', type: 'Integer', req: 'No', def: '50', desc: 'Pagination page limit size (1 - 100)' },
        { name: 'offset', type: 'Integer', req: 'No', def: '0', desc: 'Pagination offset index' }
      ],
      curlExample: 'curl -H "X-API-Key: YOUR_API_KEY" "http://localhost:8000/api/v1/public/observations?date=2023-08-25&limit=2"',
      sampleResponse: {
        meta: {
          agency: "ISRO",
          data_standard: "PDS4",
          licensing: "ISRO Open Data Sharing Policy (ISDA)",
          api_version: "1.0.0",
          rate_limit_limit: 1000,
          rate_limit_remaining: 996,
          timestamp: "2026-06-14T12:03:00.000Z"
        },
        results: [
          {
            observation_id: "LIB-20230825-104221-00",
            session_id: "CH3 LIBS v2 20230825",
            logical_identifier: "urn:isro:isda:ch3_chr.lib:data_calibrated:ch3_lib_002_20230825T104221_00_l1",
            observation_code: "ch3_lib_002_20230825T104221_00_l1",
            observation_number: 2,
            sub_index: 1,
            start_time: "2023-08-25T11:35:22",
            stop_time: "2023-08-25T11:35:23",
            pds_version_id: "1.0",
            information_model_version: "1.11.0.0",
            processing_level: "Calibrated",
            purpose: "Science",
            observation_date: "2023-08-25T00:00:00",
            target_description: "Moon is a natural satellite of Earth",
            record_count: 2
          }
        ],
        links: {
          self: "/api/v1/public/observations?limit=2&offset=0&date=2023-08-25",
          next: null,
          prev: null
        }
      }
    },
    {
      id: 'measurements',
      method: 'GET',
      path: '/public/measurements',
      description: 'List individual laser shot metadata, operational telemetry and laser parameters.',
      params: [
        { name: 'observation_id', type: 'String', req: 'Conditional', desc: 'Filter by observation code (supports LIB-... or FI-... formats)' },
        { name: 'mission', type: 'String', req: 'Conditional', desc: 'Filter by mission code (e.g. CH3) — use instead of observation_id for simpler queries' },
        { name: 'instrument', type: 'String', req: 'Optional', desc: 'Filter by instrument code (e.g. LIBS)' },
        { name: 'date', type: 'String (YYYY-MM-DD)', req: 'Conditional', desc: 'Filter by observation capture date (e.g. 2023-08-25)' },
        { name: 'is_background', type: 'Boolean', req: 'No', desc: 'True for background calibration zaps; False for surface plasma spectra' },
        { name: 'limit', type: 'Integer', req: 'No', def: '50', desc: 'Pagination limit size' },
        { name: 'offset', type: 'Integer', req: 'No', def: '0', desc: 'Pagination offset index' }
      ],
      curlExample: 'curl -H "X-API-Key: YOUR_API_KEY" "http://localhost:8000/api/v1/public/measurements?date=2023-08-25&mission=CH3&limit=5"',
      sampleResponse: {
        meta: {
          agency: "ISRO",
          data_standard: "PDS4",
          licensing: "ISRO Open Data Sharing Policy (ISDA)",
          api_version: "1.0.0",
          rate_limit_limit: 1000,
          rate_limit_remaining: 995,
          timestamp: "2026-06-14T12:04:00.000Z"
        },
        results: [
          {
            measurement_id: "FI-20230825-145453-00-1",
            observation_id: "FI-20230825-145453-00",
            measurement_index: 1,
            time_utc: "2023-08-25T16:03:35",
            measurement_count: 2,
            operation_mode: "ASLF",
            measurement_type: "EP",
            is_background: false,
            integration_time_us: 1000,
            number_of_pulses: 3,
            laser_energy_v: 3386
          }
        ],
        links: {
          self: "/api/v1/public/measurements?limit=1&offset=0&observation_id=LIB-20230825-145453-00",
          next: null,
          prev: null
        }
      }
    },
    {
      id: 'spectra_bulk',
      method: 'GET',
      path: '/public/spectra',
      description: 'Bulk retrieve processed and cleaned wavelength-intensity datasets for multiple laser shots at once.',
      params: [
        { name: 'observation_id', type: 'String', req: 'Conditional', desc: 'Fetch all spectra for an observation session ID (e.g. LIB-20230825-145453-00)' },
        { name: 'date', type: 'String (YYYY-MM-DD)', req: 'Conditional', desc: 'Fetch all spectra captured on a specific date' },
        { name: 'mission', type: 'String', req: 'Conditional', desc: 'Filter by mission code (e.g. CH3) — combine with date for targeted queries' },
        { name: 'measurement_ids', type: 'String (CSV list)', req: 'Conditional', desc: 'Filter explicitly by comma-separated measurement IDs (e.g. FI-20230825-104221-00-1)' },
        { name: 'lambda_min', type: 'Float', req: 'No', def: '164.35', desc: 'Lower wavelength limit boundary in nm' },
        { name: 'lambda_max', type: 'Float', req: 'No', def: '878.26', desc: 'Upper wavelength limit boundary in nm' },
        { name: 'downsample', type: 'Boolean', req: 'No', def: 'false', desc: 'True to activate Largest Triangle Three Buckets (LTTB) downsampling' },
        { name: 'zoom_level', type: 'Integer', req: 'No', def: '0', desc: 'Downsample resolution level (0 = coarsest, 5 = highest resolution)' },
        { name: 'target_wavelengths', type: 'String (CSV list)', req: 'No', desc: 'Comma-separated NIST wavelengths to preserve during downsampling' },
        { name: 'limit', type: 'Integer', req: 'No', def: '10', desc: 'Limit the number of spectral profiles returned (max 50)' },
        { name: 'offset', type: 'Integer', req: 'No', def: '0', desc: 'Pagination offset index' }
      ],
      curlExample: 'curl -H "X-API-Key: YOUR_API_KEY" "http://localhost:8000/api/v1/public/spectra?observation_id=LIB-20230825-145453-00&downsample=true&zoom_level=1"',
      sampleResponse: {
        meta: {
          agency: "ISRO",
          data_standard: "PDS4",
          licensing: "ISRO Open Data Sharing Policy (ISDA)",
          api_version: "1.0.0",
          rate_limit_limit: 1000,
          rate_limit_remaining: 994,
          timestamp: "2026-06-14T12:05:00.000Z"
        },
        results: [
          {
            measurement_id: "FI-20230825-145453-00-1",
            processing_level: "Calibrated",
            points_count: 1047,
            wavelength_range: { min: 164.35, max: 878.26 },
            data: [
              { wavelength_nm: 164.35, intensity: 45.3, raw_intensity: 45.3 },
              { wavelength_nm: 164.68, intensity: 47.1, raw_intensity: 47.1 }
            ]
          }
        ],
        links: {
          self: "/api/v1/public/spectra?limit=10&offset=0&observation_id=LIB-20230825-145453-00",
          next: null,
          prev: null
        }
      }
    },
    {
      id: 'spectra_detail',
      method: 'GET',
      path: '/public/spectra/{id}',
      description: 'Fetch the full raw or downsampled spectral channels dataset for a single laser shot.',
      params: [
        { name: 'id', type: 'String (Path)', req: true, desc: 'Target measurement ID, e.g., FI-20230825-145453-00-1' },
        { name: 'lambda_min', type: 'Float', req: false, def: '164.35', desc: 'Wavelength lower boundary (nm)' },
        { name: 'lambda_max', type: 'Float', req: false, def: '878.26', desc: 'Wavelength upper boundary (nm)' },
        { name: 'downsample', type: 'Boolean', req: false, def: 'false', desc: 'Enable LTTB downsampling' },
        { name: 'zoom_level', type: 'Integer', req: false, def: '0', desc: 'LTTB zoom level (0-5)' },
        { name: 'target_wavelengths', type: 'String (CSV list)', req: false, desc: 'Wavelength channels to preserve' }
      ],
      curlExample: 'curl -H "X-API-Key: YOUR_API_KEY" "http://localhost:8000/api/v1/public/spectra/FI-20230825-145453-00-1?downsample=true"',
      sampleResponse: {
        meta: {
          agency: "ISRO",
          data_standard: "PDS4",
          licensing: "ISRO Open Data Sharing Policy (ISDA)",
          api_version: "1.0.0",
          rate_limit_limit: 1000,
          rate_limit_remaining: 994,
          timestamp: "2026-06-14T12:06:00.000Z"
        },
        results: {
          measurement_id: "FI-20230825-145453-00-1",
          processing_level: "Calibrated",
          points_count: 2094,
          wavelength_range: { min: 164.35, max: 878.26 },
          data: [
            { wavelength_nm: 164.35, intensity: 45.3, raw_intensity: 45.3 }
          ]
        },
        links: {
          self: "/api/v1/public/spectra/FI-20230825-145453-00-1"
        }
      }
    }
  ];

  const snippets = {
    curl: `# Fetch list of space missions
curl -H "X-API-Key: ${customKey}" \\
     "http://localhost:8000/api/v1/public/missions?limit=5"

# Fetch downsampled bulk spectrum with peak preservation
curl -H "X-API-Key: ${customKey}" \\
     "http://localhost:8000/api/v1/public/spectra?observation_id=LIB-20230825-145453-00&downsample=true&zoom_level=1"`,

    python: `import requests

# Base configuration
base_url = "http://localhost:8000/api/v1/public"
headers = {"X-API-Key": "${customKey}"}

# 1. Fetch space missions
response = requests.get(f"{base_url}/missions", headers=headers, params={"limit": 5})
missions = response.json()
print("Missions:", [m["mission_code"] for m in missions["results"]])

# 2. Query observations by date
obs_response = requests.get(
    f"{base_url}/observations", 
    headers=headers, 
    params={"mission": "CH3", "date": "2023-08-25"}
)
print("Observations found on date:", len(obs_response.json()["results"]))

# 3. Retrieve spectrum points in bulk
spec_response = requests.get(
    f"{base_url}/spectra",
    headers=headers,
    params={
        "observation_id": "LIB-20230825-145453-00",
        "downsample": "true",
        "zoom_level": 1,
        "target_wavelengths": "393.37,396.15"
    }
)
spec_data = spec_response.json()
print(f"Spectral products returned: {len(spec_data['results'])}")`,

    node: `const axios = require('axios');

const apiBase = 'http://localhost:8000/api/v1/public';
const headers = { 'X-API-Key': '${customKey}' };

async function fetchLunarData() {
  try {
    // 1. Fetch missions list
    const resMissions = await axios.get(\`\${apiBase}/missions?limit=5\`, { headers });
    console.log('Missions cataloged:', resMissions.data.results.map(m => m.mission_code));

    // 2. Fetch bulk spectrum (downsampled)
    const resSpectrum = await axios.get(\`\${apiBase}/spectra\`, {
      headers,
      params: { 
        observation_id: 'LIB-20230825-145453-00',
        downsample: true, 
        zoom_level: 2 
      }
    });
    console.log('Bulk profiles:', resSpectrum.data.results.length);
  } catch (error) {
    console.error('API Error:', error.response?.data || error.message);
  }
}

fetchLunarData();`,

    go: `package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

func main() {
	client := &http.Client{}
	req, _ := http.NewRequest("GET", "http://localhost:8000/api/v1/public/missions?limit=2", nil)
	req.Header.Set("X-API-Key", "${customKey}")

	resp, err := client.Do(req)
	if err != nil {
		fmt.Printf("Request error: %v\\n", err)
		return
	}
	defer resp.Body.Close()

	bodyBytes, _ := io.ReadAll(resp.Body)
	var result map[string]interface{}
	json.Unmarshal(bodyBytes, &result)

	fmt.Println("API Envelope Meta:", result["meta"])
}`,

    r: `library(httr)
library(jsonlite)

base_url <- "http://localhost:8000/api/v1/public"
api_key <- "${customKey}"

# Fetch list of science observations
res <- GET(
  url = paste0(base_url, "/observations"),
  add_headers("X-API-Key" = api_key),
  query = list(limit = 10, mission = "CH3", date = "2023-08-25")
)

data <- fromJSON(content(res, "text", encoding = "UTF-8"))
print(data$results)
`
  };

  const postmanCollectionJson = {
    "info": {
      "name": "LunarAtlas Public Developer API Reference",
      "description": "Automated Postman Collection mapping all public catalog routes and data streams of the LunarAtlas space science database.",
      "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "item": [
      {
        "name": "Missions Catalog",
        "request": {
          "method": "GET",
          "header": [{"key": "X-API-Key", "value": "{{API_KEY}}"}],
          "url": {
            "raw": "{{BASE_URL}}/public/missions?limit=10&offset=0",
            "host": ["{{BASE_URL}}"],
            "path": ["public", "missions"],
            "query": [
              {"key": "limit", "value": "10", "description": "Pagination size limit"},
              {"key": "offset", "value": "0", "description": "Pagination index offset"}
            ]
          }
        }
      },
      {
        "name": "Mission Details",
        "request": {
          "method": "GET",
          "header": [{"key": "X-API-Key", "value": "{{API_KEY}}"}],
          "url": {
            "raw": "{{BASE_URL}}/public/missions/:code",
            "host": ["{{BASE_URL}}"],
            "path": ["public", "missions", ":code"],
            "variable": [
              {"key": "code", "value": "CH3", "description": "Target mission code (case-insensitive)"}
            ]
          }
        }
      },
      {
        "name": "Instruments Catalog",
        "request": {
          "method": "GET",
          "header": [{"key": "X-API-Key", "value": "{{API_KEY}}"}],
          "url": {
            "raw": "{{BASE_URL}}/public/instruments?mission_code=CH3",
            "host": ["{{BASE_URL}}"],
            "path": ["public", "instruments"],
            "query": [
              {"key": "mission_code", "value": "CH3", "description": "Filter by mission short code"}
            ]
          }
        }
      },
      {
        "name": "Observations Catalog",
        "request": {
          "method": "GET",
          "header": [{"key": "X-API-Key", "value": "{{API_KEY}}"}],
          "url": {
            "raw": "{{BASE_URL}}/public/observations?mission=CH3&instrument=LIBS&date=2023-08-25&limit=50&offset=0",
            "host": ["{{BASE_URL}}"],
            "path": ["public", "observations"],
            "query": [
              {"key": "mission", "value": "CH3", "description": "Mission code filter"},
              {"key": "instrument", "value": "LIBS", "description": "Instrument code filter"},
              {"key": "target_name", "value": "Moon", "disabled": true, "description": "Filter by target body"},
              {"key": "date", "value": "2023-08-25", "description": "Observation date (YYYY-MM-DD)"},
              {"key": "limit", "value": "50"},
              {"key": "offset", "value": "0"}
            ]
          }
        }
      },
      {
        "name": "Measurements Telemetry",
        "request": {
          "method": "GET",
          "header": [{"key": "X-API-Key", "value": "{{API_KEY}}"}],
          "url": {
            "raw": "{{BASE_URL}}/public/measurements?date=2023-08-25&mission=CH3&limit=50&offset=0",
            "host": ["{{BASE_URL}}"],
            "path": ["public", "measurements"],
            "query": [
              {"key": "observation_id", "value": "LIB-20230825-145453-00", "disabled": true, "description": "Observation session ID"},
              {"key": "mission", "value": "CH3"},
              {"key": "instrument", "value": "LIBS", "disabled": true},
              {"key": "date", "value": "2023-08-25"},
              {"key": "is_background", "value": "false", "disabled": true, "description": "True for background, False for surface plasma"},
              {"key": "limit", "value": "50"},
              {"key": "offset", "value": "0"}
            ]
          }
        }
      },
      {
        "name": "Spectra Bulk Retrieval",
        "request": {
          "method": "GET",
          "header": [{"key": "X-API-Key", "value": "{{API_KEY}}"}],
          "url": {
            "raw": "{{BASE_URL}}/public/spectra?observation_id=LIB-20230825-145453-00&downsample=true&zoom_level=1&limit=10&offset=0",
            "host": ["{{BASE_URL}}"],
            "path": ["public", "spectra"],
            "query": [
              {"key": "observation_id", "value": "LIB-20230825-145453-00"},
              {"key": "date", "value": "2023-08-25", "disabled": true},
              {"key": "mission", "value": "CH3", "disabled": true},
              {"key": "measurement_ids", "value": "FI-20230825-145453-00-1", "disabled": true},
              {"key": "lambda_min", "value": "164.35", "disabled": true},
              {"key": "lambda_max", "value": "878.26", "disabled": true},
              {"key": "downsample", "value": "true"},
              {"key": "zoom_level", "value": "1"},
              {"key": "target_wavelengths", "value": "393.37,396.15", "disabled": true},
              {"key": "limit", "value": "10"},
              {"key": "offset", "value": "0"}
            ]
          }
        }
      },
      {
        "name": "Single Spectrum Detail",
        "request": {
          "method": "GET",
          "header": [{"key": "X-API-Key", "value": "{{API_KEY}}"}],
          "url": {
            "raw": "{{BASE_URL}}/public/spectra/:id?downsample=false",
            "host": ["{{BASE_URL}}"],
            "path": ["public", "spectra", ":id"],
            "query": [
              {"key": "lambda_min", "value": "164.35", "disabled": true},
              {"key": "lambda_max", "value": "878.26", "disabled": true},
              {"key": "downsample", "value": "false"},
              {"key": "zoom_level", "value": "0", "disabled": true},
              {"key": "target_wavelengths", "value": "393.37,396.15", "disabled": true}
            ],
            "variable": [
              {"key": "id", "value": "FI-20230825-145453-00-1", "description": "Target measurement ID"}
            ]
          }
        }
      }
    ],
    "variable": [
      {"key": "BASE_URL", "value": "http://localhost:8000/api/v1", "type": "string"},
      {"key": "API_KEY", "value": "YOUR_API_KEY", "type": "string"}
    ]
  };

  function downloadPostmanCollection() {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(postmanCollectionJson, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", "lunaratlas_postman_collection.json");
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  }



  return (
    <div className="bg-canvas dark:bg-[#0d0d0d] transition-colors duration-200 overflow-x-hidden">
      
      {/* Hero Header */}
      <section className="border-b border-gray-200 dark:border-[#1e1e1e] bg-[#f8f9fa] dark:bg-[#141414] py-14">
        <div className="max-w-[1400px] mx-auto px-8">
          <div className="text-[9px] font-bold tracking-[3px] text-neutral-700 dark:text-neutral-400 uppercase mb-3">
            Open Science Catalogs
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-neutral-900 dark:text-white m-0 mb-4">
            LunarAtlas Public API
          </h1>
          <p className="text-[13.5px] text-gray-600 dark:text-neutral-300 leading-relaxed max-w-[760px] m-0">
            A PDS4-compliant REST API serving normalized space science products. Integrate raw or downsampled 
            laser-induced breakdown spectroscopy (LIBS) data directly into your analytical pipelines, python notebooks, 
            and research systems.
          </p>
        </div>
      </section>

      {/* Main Layout grid */}
      <div className="max-w-[1400px] mx-auto px-8 py-12 grid grid-cols-1 xl:grid-cols-[1fr_380px] gap-12 items-start">
        
        {/* Left column: Student Guide & Reference Docs */}
        <div className="space-y-12 min-w-0">
          
          {/* Quickstart Guide for Students and First-time Users */}
          <section className="bg-white dark:bg-[#111] border border-neutral-200 dark:border-[#222] p-8 rounded-lg shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <span className="bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300 text-[10px] font-black tracking-widest uppercase px-2 py-0.5 rounded-sm">
                Student &amp; Researcher Guide
              </span>
              <h2 className="text-[16px] font-bold text-neutral-900 dark:text-neutral-100 m-0 tracking-tight">First-Time Integration Guide</h2>
            </div>
            <p className="text-[13px] text-neutral-800 dark:text-neutral-300 leading-relaxed mb-6">
              Welcome to the LunarAtlas developer portal! If you are a student, educator, or independent researcher looking to access actual Chandrayaan-3 LIBS datasets programmatically, follow these three steps to make your first API request:
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="border border-neutral-100 dark:border-[#222] p-5 rounded bg-gray-50/50 dark:bg-[#161616]/50">
                <div className="w-6 h-6 rounded-full bg-black dark:bg-[#e0e0e0] text-white dark:text-black flex items-center justify-center text-[11px] font-bold mb-3">1</div>
                <div className="text-[12px] font-bold text-neutral-800 dark:text-neutral-200 mb-1.5">Create a Profile</div>
                <div className="text-[11.5px] text-neutral-700 dark:text-neutral-300 leading-normal">
                  <span className="font-semibold text-neutral-800 dark:text-neutral-200">Sign Up</span> for a free account. Update your role (e.g. <em>Student</em> or <em>Academic</em>) inside the user profile setup.
                </div>
              </div>
              <div className="border border-neutral-100 dark:border-[#222] p-5 rounded bg-gray-50/50 dark:bg-[#161616]/50">
                <div className="w-6 h-6 rounded-full bg-black dark:bg-[#e0e0e0] text-white dark:text-black flex items-center justify-center text-[11px] font-bold mb-3">2</div>
                <div className="text-[12px] font-bold text-neutral-800 dark:text-neutral-200 mb-1.5">Generate your API Key</div>
                <div className="text-[11.5px] text-neutral-700 dark:text-neutral-300 leading-normal">
                  Go to your <Link to="/dashboard" className="text-black dark:text-white font-semibold underline">Dashboard</Link> &rarr; API Keys tab. Generate a new key. Copy it immediately as it will only be shown once.
                </div>
              </div>
              <div className="border border-neutral-100 dark:border-[#222] p-5 rounded bg-gray-50/50 dark:bg-[#161616]/50">
                <div className="w-6 h-6 rounded-full bg-black dark:bg-[#e0e0e0] text-white dark:text-black flex items-center justify-center text-[11px] font-bold mb-3">3</div>
                <div className="text-[12px] font-bold text-neutral-800 dark:text-neutral-200 mb-1.5">Query the Catalog</div>
                <div className="text-[11.5px] text-neutral-700 dark:text-neutral-300 leading-normal">
                  Pass the token inside the HTTP request header: <br/><code className={CODE}>X-API-Key: la_7f3...</code> or parameter: <br/><code className={CODE}>?api_key=la_7f3...</code>.
                </div>
              </div>
            </div>

            {/* ID Discovery & Construction Guide */}
            <div className="mt-8 pt-6 border-t border-neutral-100 dark:border-[#222]">
              <h3 className="text-[13px] font-bold text-neutral-900 dark:text-neutral-100 mb-2">How to Discover or Construct Identifiers</h3>
              <p className="text-[12.5px] text-neutral-800 dark:text-neutral-300 leading-relaxed mb-4">
                To query specific measurements or spectral details, you will need identifiers like <code className="font-semibold text-neutral-800 dark:text-neutral-200">observation_id</code> or <code className="font-semibold text-neutral-800 dark:text-neutral-200">measurement_id</code>. You can obtain these in two ways:
              </p>
              <div className="space-y-4">
                <div className="text-[12px]">
                  <span className="font-bold text-gray-800 dark:text-neutral-200 block mb-1">Method 1: Dynamic Discovery (Query-First API Workflow)</span>
                  <p className="text-gray-500 dark:text-neutral-400 m-0 pl-4 leading-normal">
                    Call the list endpoints first to search for records. For example, make a request to <code className={CODE}>GET /public/observations?date=2023-08-25</code>. Copy the returned <code className="text-black dark:text-white font-mono text-[11px] font-bold">observation_id</code> (e.g. <code className="font-mono text-[11px]">LIB-20230825-145453-00</code>) to query its child measurements, or copy the <code className="text-black dark:text-white font-mono text-[11px] font-bold">measurement_id</code> (e.g. <code className="font-mono text-[11px]">FI-20230825-145453-00-1</code>) to fetch its raw spectrum.
                  </p>
                </div>
                <div className="text-[12px]">
                  <span className="font-bold text-gray-800 dark:text-neutral-200 block mb-1">Method 2: Static Mapping (Matching the ISRO PRADAN structure)</span>
                  <p className="text-gray-500 dark:text-neutral-400 m-0 pl-4 leading-normal">
                    The database identifiers are mapped deterministically from the physical file structures on disk:
                  </p>
                  <ul className="list-disc pl-8 space-y-1 mt-2 text-gray-500 dark:text-neutral-400 leading-normal">
                    <li><strong>Observation ID:</strong> Matches the session folder name formatted as <code className="font-mono text-[11px]">LIB-YYYYMMDD-HHMMSS-SS</code> (e.g. folder <code className="font-mono text-[11px] text-gray-700 dark:text-neutral-300">ch3_lib_002_20230825T145453_00_l1</code> maps to ID <code className="font-mono text-[11px] text-black dark:text-white">LIB-20230825-145453-00</code>).</li>
                    <li><strong>Measurement ID:</strong> Matches the individual shot CSV file suffix formatted as <code className="font-mono text-[11px]">FI-YYYYMMDD-HHMMSS-SS-X</code> (e.g. file <code className="font-mono text-[11px] text-gray-700 dark:text-neutral-300">ch3_lib_002_20230825T145453_00_l1_0_1.csv</code> maps to ID <code className="font-mono text-[11px] text-black dark:text-white">FI-20230825-145453-00-1</code>).</li>
                  </ul>
                </div>
              </div>
            </div>
          </section>

          {/* Recommended Workflows Section */}
          <section className="bg-white dark:bg-[#0f0f11] border border-neutral-200 dark:border-neutral-800 p-8 rounded-xl shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <span className="bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-300 text-[10px] font-bold tracking-widest uppercase px-2.5 py-1 rounded-md border border-neutral-200 dark:border-neutral-700">
                Recommended Access Patterns
              </span>
              <h2 className="text-[16px] font-bold text-neutral-900 dark:text-[#f0f0f0] m-0 tracking-tight">Flexible Query Workflows</h2>
            </div>
            <p className="text-[13px] text-neutral-800 dark:text-neutral-300 leading-relaxed mb-6">
              Depending on your research goals, you can navigate the data catalog using one of three standard patterns. Note how the newer cascading filters allow you to skip the entity hierarchy entirely:
            </p>

            <div className="space-y-4">
              {/* Pattern A */}
              <div className="border border-neutral-100 dark:border-[#222] p-4 rounded bg-gray-50/50 dark:bg-[#161616]/50">
                <div className="flex justify-between items-start mb-2">
                  <div className="text-[12px] font-bold text-gray-800 dark:text-neutral-200 flex items-center gap-2">
                    <span className="text-black dark:text-white font-mono">Pattern A</span>
                    <span>Hierarchical Catalog Browsing</span>
                  </div>
                  <span className="text-[10px] text-neutral-800 dark:text-neutral-300 font-semibold">Standard PDS Flow</span>
                </div>
                <p className="text-[11.5px] text-neutral-700 dark:text-neutral-300 m-0 mb-3">
                  Start by listing observations on a specific date, retrieve the matching ID, then query for its spectra. Best for broad catalog exploration.
                </p>
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2 font-mono text-[10.5px]">
                    <span className="bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 px-1 py-0.5 rounded text-[9px] font-bold">GET</span>
                    <span className="text-neutral-800 dark:text-neutral-200">/public/observations?date=2023-08-25</span>
                  </div>
                  <div className="text-neutral-700 dark:text-neutral-300 text-[10px] pl-8">&darr; Extracts observation_id, e.g., <code className="font-semibold text-neutral-800 dark:text-neutral-300">LIB-20230825-145453-00</code></div>
                  <div className="flex items-center gap-2 font-mono text-[10.5px]">
                    <span className="bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 px-1 py-0.5 rounded text-[9px] font-bold">GET</span>
                    <span className="text-neutral-800 dark:text-neutral-200">/public/spectra?observation_id=LIB-20230825-145453-00</span>
                  </div>
                </div>
              </div>

              {/* Pattern B */}
              <div className="border border-neutral-200 dark:border-neutral-800 p-4 rounded-lg bg-neutral-50/40 dark:bg-neutral-900/25">
                <div className="flex justify-between items-start mb-2">
                  <div className="text-[12px] font-bold text-neutral-800 dark:text-neutral-200 flex items-center gap-2">
                    <span className="font-mono">Pattern B</span>
                    <span>Direct Filtering (Cascading Query)</span>
                  </div>
                  <span className="text-[10px] text-neutral-800 dark:text-neutral-300 font-bold uppercase tracking-wider bg-neutral-200/70 dark:bg-neutral-800/80 px-1.5 py-0.5 rounded-sm">Recommended</span>
                </div>
                <p className="text-[11.5px] text-neutral-700 dark:text-neutral-300 m-0 mb-3">
                  Query spectra or measurements directly by specifying the mission code and date. This bypasses the need to look up internal observation IDs.
                </p>
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2 font-mono text-[10.5px]">
                    <span className="bg-neutral-200/80 text-neutral-800 dark:bg-neutral-800/80 dark:text-neutral-300 px-1 py-0.5 rounded text-[9px] font-bold">GET</span>
                    <span className="text-neutral-800 dark:text-neutral-200">/public/measurements?date=2023-08-25&amp;mission=CH3</span>
                  </div>
                  <div className="flex items-center gap-2 font-mono text-[10.5px]">
                    <span className="bg-neutral-200/80 text-neutral-800 dark:bg-neutral-800/80 dark:text-neutral-300 px-1 py-0.5 rounded text-[9px] font-bold">GET</span>
                    <span className="text-neutral-800 dark:text-neutral-200">/public/spectra?date=2023-08-25&amp;mission=CH3</span>
                  </div>
                </div>
              </div>

              {/* Pattern C */}
              <div className="border border-neutral-100 dark:border-[#222] p-4 rounded bg-gray-50/50 dark:bg-[#161616]/50">
                <div className="flex justify-between items-start mb-2">
                  <div className="text-[12px] font-bold text-gray-800 dark:text-neutral-200 flex items-center gap-2">
                    <span className="text-black dark:text-white font-mono">Pattern C</span>
                    <span>Specific Record Retrieval</span>
                  </div>
                  <span className="text-[10px] text-neutral-800 dark:text-neutral-300 font-semibold">Direct Access</span>
                </div>
                <p className="text-[11.5px] text-neutral-700 dark:text-neutral-300 m-0 mb-3">
                  If you already know the unique identifier for a specific laser shot/measurement, retrieve its high-resolution spectral channels directly.
                </p>
                <div className="flex items-center gap-2 font-mono text-[10.5px]">
                  <span className="bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 px-1 py-0.5 rounded text-[9px] font-bold">GET</span>
                  <span className="text-neutral-800 dark:text-neutral-200">/public/spectra/FI-20230825-145453-00-1</span>
                </div>
              </div>
            </div>
          </section>

          {/* Section: Overview */}
          <section className="bg-white dark:bg-[#121212] p-8 border border-gray-200 dark:border-[#222] rounded-lg shadow-sm">
            <h2 className="text-xl font-bold tracking-tight text-neutral-900 dark:text-neutral-100 mt-0 mb-3">API Overview</h2>
            <div className="text-[13px] text-gray-600 dark:text-[#b0b0b0] leading-[1.8] space-y-4">
              <p>
                To support peer-reviewable planetary research, LunarAtlas exposes standard catalog REST APIs for spectral 
                data and instrumentation metadata. The database schemas conform strictly to standardized 
                <strong> PDS4 Specifications</strong>.
              </p>
              <p>
                We serve structured space mission indexes, instrument telemetry logs, laser parameters, and 
                individual spectral channels containing 2,094 calibrated wavelength steps. This replaces manual downloading 
                of massive raw archives from space science data centers.
              </p>
            </div>
          </section>

          {/* Section: Standard Response Envelope */}
          <section className="bg-white dark:bg-[#121212] p-8 border border-gray-200 dark:border-[#222] rounded-lg shadow-sm">
            <h2 className="text-xl font-bold tracking-tight text-neutral-900 dark:text-neutral-100 mt-0 mb-3">Standard Response Envelope</h2>
            <p className="text-[13px] text-gray-600 dark:text-[#b0b0b0] leading-[1.75] mb-4">
              All responses are wrapped in a standard metadata envelope detailing space agency licensing, schema standards, and rate limits:
            </p>
            <pre className={CODEBLK}>{`{
  "meta": {
    "agency": "ISRO",
    "data_standard": "PDS4",
    "licensing": "ISRO Open Data Sharing Policy (ISDA)",
    "api_version": "1.0.0",
    "rate_limit_limit": 1000,
    "rate_limit_remaining": 994,
    "timestamp": "2026-06-14T12:00:00.000Z"
  },
  "results": { ... },
  "links": {
    "self": "/api/v1/public/spectra?limit=10&offset=0",
    "next": null,
    "prev": null
  }
}`}</pre>
          </section>

          {/* Section: Interactive API Route Documentation */}
          <section className="bg-white dark:bg-[#121212] p-8 border border-gray-200 dark:border-[#222] rounded-lg shadow-sm">
            <h2 className="text-xl font-bold tracking-tight text-neutral-900 dark:text-neutral-100 mt-0 mb-2">Endpoint Reference Catalog</h2>
            <p className="text-[13px] text-neutral-700 dark:text-neutral-300 mb-6">
              Click any API route below to view parameter definitions, sample requests, and complete JSON response layouts.
            </p>

            <div className="space-y-4">
              {endpointDocs.map((doc) => {
                const isExpanded = expandedEndpoint === doc.id;
                return (
                  <div 
                    key={doc.id}
                    className={`border border-solid rounded-lg transition-all duration-150 ${
                      isExpanded 
                        ? 'border-black dark:border-white bg-[#fafafa]/50 dark:bg-[#161616]/40' 
                        : 'border-gray-200 dark:border-[#222] hover:border-gray-300 dark:hover:border-[#333]'
                    }`}
                  >
                    {/* Header line click toggle */}
                    <button
                      onClick={() => setExpandedEndpoint(isExpanded ? null : doc.id)}
                      className="w-full text-left py-3.5 px-5 flex items-center justify-between bg-transparent border-0 cursor-pointer"
                    >
                      <div className="flex items-center gap-3 flex-wrap">
                        <span className="font-mono text-[9px] font-bold px-2 py-0.5 rounded border border-neutral-200 dark:border-neutral-700 bg-neutral-100 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300">
                          {doc.method}
                        </span>
                        <code className="font-mono text-[12px] font-bold text-gray-800 dark:text-neutral-200">
                          {doc.path}
                        </code>
                      </div>
                      <span className="text-[11.5px] text-neutral-800 dark:text-neutral-300">
                        {isExpanded ? 'Collapse ▲' : 'Expand ▼'}
                      </span>
                    </button>

                    {isExpanded && (
                      <div className="px-5 pb-6 border-t border-solid border-gray-100 dark:border-[#222] pt-4 space-y-4">
                        <p className="text-[13px] text-neutral-800 dark:text-neutral-300 leading-relaxed m-0">
                          {doc.description}
                        </p>

                        {/* Parameter list */}
                        <div>
                          <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-800 dark:text-neutral-300 mb-2">Parameters</div>
                          <div className="overflow-x-auto border border-solid border-neutral-100 dark:border-[#222] rounded">
                            <table className={TABLE}>
                              <thead>
                                <tr className="bg-gray-50/50 dark:bg-[#161616]/60 border-b border-gray-200 dark:border-[#222]">
                                  <th className={TH}>Name</th>
                                  <th className={TH}>Type</th>
                                  <th className={TH}>Required</th>
                                  <th className={TH}>Default</th>
                                  <th className={TH}>Description</th>
                                </tr>
                              </thead>
                              <tbody>
                                {doc.params.map((p) => (
                                  <tr key={p.name} className="border-b border-gray-100 dark:border-[#1e1e1e]/50 last:border-0 hover:bg-gray-50/10">
                                    <td className="py-2.5 px-4 font-mono font-bold text-[11.5px] text-neutral-800 dark:text-neutral-200">{p.name}</td>
                                    <td className="py-2.5 px-4 text-neutral-700 dark:text-neutral-300">{p.type}</td>
                                    <td className="py-2.5 px-4 font-semibold text-[11px]">
                                      {typeof p.req === 'string' ? (
                                        <span className={
                                          p.req === 'Required' ? 'text-red-600 dark:text-red-400' :
                                          p.req === 'Recommended' ? 'text-green-600 dark:text-green-400' :
                                          p.req === 'Conditional' ? 'text-black dark:text-white font-medium' :
                                          'text-neutral-700 dark:text-neutral-300'
                                        }>
                                          {p.req}
                                        </span>
                                      ) : p.req ? (
                                        <span className="text-red-600 dark:text-red-400">Yes</span>
                                      ) : (
                                        <span className="text-neutral-700 dark:text-neutral-300">No</span>
                                      )}
                                    </td>
                                    <td className="py-2.5 px-4 font-mono text-neutral-800 dark:text-neutral-300">{p.def || '—'}</td>
                                    <td className="py-2.5 px-4 text-neutral-700 dark:text-neutral-300 leading-normal">{p.desc}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>

                        {/* Copyable cURL preview */}
                        <div>
                          <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-800 dark:text-neutral-300 mb-2">Request Example (cURL)</div>
                          <pre className={CODEBLK}>{doc.curlExample}</pre>
                        </div>

                        {/* Expected JSON Response Schema block */}
                        <div>
                          <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-800 dark:text-neutral-300 mb-2">Expected JSON Response</div>
                          <pre className={`${CODEBLK} max-h-[300px]`}>
                            {JSON.stringify(doc.sampleResponse, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </section>

          {/* Section: Integration Guides (Multi-language template) */}
          <section className="bg-white dark:bg-[#121212] p-8 border border-gray-200 dark:border-[#222] rounded-lg shadow-sm">
            <h2 className="text-xl font-bold tracking-tight text-neutral-900 dark:text-neutral-100 mb-2 font-sans">Multi-Language Code Snippets</h2>
            <p className="text-[13px] text-neutral-700 dark:text-neutral-300 mb-5 leading-normal">
              Copy this bootstrap client code directly into your local scripts or Jupyter Notebooks to begin querying LunarAtlas.
            </p>

            {/* Snippet Tabs */}
            <div className="flex border-b border-gray-200 dark:border-[#222] mb-4">
              {(['curl', 'python', 'node', 'go', 'r'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveSnippetTab(tab)}
                  className={`px-4 py-2 text-[11px] font-bold tracking-wider uppercase border-b-2 cursor-pointer transition-all bg-transparent ${
                    activeSnippetTab === tab
                      ? 'border-black text-black dark:border-white dark:text-white'
                      : 'border-transparent text-neutral-700 hover:text-neutral-900 dark:text-neutral-300 dark:hover:text-white'
                  }`}
                >
                  {tab === 'node' ? 'Node.js' : tab === 'curl' ? 'cURL' : tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>

            <pre className={CODEBLK}>{snippets[activeSnippetTab]}</pre>
          </section>

          {/* Section: Postman */}
          <section className="bg-white dark:bg-[#121212] p-8 border border-gray-200 dark:border-[#222] rounded-lg shadow-sm">
            <h2 className="text-xl font-bold tracking-tight text-neutral-900 dark:text-neutral-100 mb-3">Postman Workspace Schema</h2>
            <div className="text-[13px] text-neutral-800 dark:text-neutral-300 leading-[1.75]">
              <p className="mb-4">
                We maintain an up-to-date Postman API schema. Import this collection into your Postman 
                client to run automated queries and visualize raw lunar response models.
              </p>
              <button
                onClick={downloadPostmanCollection}
                className="inline-flex items-center gap-2 border border-black bg-transparent text-black hover:bg-gray-100 dark:border-white dark:text-white dark:hover:bg-gray-900 font-bold text-[11px] tracking-wider uppercase px-5 py-2.5 rounded cursor-pointer transition-colors"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download Postman Collection
              </button>
            </div>
          </section>

        </div>
        
        {/* Right column: Interactive Console Sidebar */}
        <aside className="sticky top-[80px] space-y-6 min-w-0 w-full overflow-hidden">
            {/* Key verification card */}
          <div className="bg-white dark:bg-[#0f0f11] border border-neutral-200 dark:border-neutral-800 p-6 rounded-xl shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-800 dark:text-neutral-300">API Playground</span>
            </div>
            
            <label className="block text-[9.5px] font-bold uppercase tracking-wide text-neutral-800 dark:text-neutral-300 mb-1.5">Enter API Authorization Key</label>
            <input
              type="text"
              className="w-full text-[12px] bg-canvas dark:bg-[#18181d] border border-neutral-300 dark:border-neutral-800 px-3.5 py-2.5 text-neutral-900 dark:text-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-700 focus:border-neutral-400 dark:focus:border-neutral-700 transition-all font-mono"
              placeholder="Paste your generated API key (la_xxxx...)"
              value={customKey}
              onChange={(e) => setCustomKey(e.target.value)}
            />
            
            <div className="mt-3 flex gap-2">
              <button 
                onClick={() => setCustomKey('')}
                className="px-4 py-1.5 border border-neutral-300 dark:border-neutral-800 text-neutral-800 dark:text-neutral-300 hover:text-neutral-950 dark:hover:text-white hover:border-neutral-400 dark:hover:border-neutral-600 bg-transparent text-[10px] font-bold uppercase tracking-wider rounded-lg cursor-pointer transition-all duration-150"
              >
                Clear
              </button>
            </div>
            
            <p className="text-[10.5px] text-neutral-400 leading-normal mt-3.5 m-0">
              Generate your custom API key from the Dashboard and paste it above to execute interactive API requests.
            </p>
          </div>

          <InteractiveApiConsole apiKey={customKey} />
        </aside>

      </div>
    </div>
  );
}

function InteractiveApiConsole({ apiKey }: { apiKey: string }) {
  const [endpoint, setEndpoint] = useState('/public/missions');
  
  // Query parameters state
  const [mission, setMission] = useState('CH3');
  const [instrument, setInstrument] = useState('LIBS');
  const [targetName, setTargetName] = useState('Moon');
  const [date, setDate] = useState('2023-08-25');
  const [observationId, setObservationId] = useState('LIB-20230825-145453-00');
  const [measurementId, setMeasurementId] = useState('FI-20230825-145453-00-1');
  const [limit, setLimit] = useState(5);
  const [offset, setOffset] = useState(0);
  const [downsample, setDownsample] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(0);
  const [targetWavelengths, setTargetWavelengths] = useState('');

  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [copyStatus, setCopyStatus] = useState<'copy' | 'copied'>('copy');

  // Generate live cURL preview reflecting state parameters
  const liveCurlCommand = useMemo(() => {
    let url = `http://localhost:8000/api/v1${endpoint}`;
    const queryParts = [];
    
    if (endpoint === '/public/missions') {
      if (limit !== 5) queryParts.push(`limit=${limit}`);
      if (offset !== 0) queryParts.push(`offset=${offset}`);
    } else if (endpoint === '/public/missions/{code}') {
      url = `http://localhost:8000/api/v1/public/missions/${mission}`;
    } else if (endpoint === '/public/instruments') {
      if (mission) queryParts.push(`mission_code=${mission}`);
    } else if (endpoint === '/public/observations') {
      if (mission) queryParts.push(`mission=${mission}`);
      if (instrument) queryParts.push(`instrument=${instrument}`);
      if (targetName) queryParts.push(`target_name=${targetName}`);
      if (date) queryParts.push(`date=${date}`);
      if (limit !== 5) queryParts.push(`limit=${limit}`);
      if (offset !== 0) queryParts.push(`offset=${offset}`);
    } else if (endpoint === '/public/measurements') {
      if (observationId) queryParts.push(`observation_id=${observationId}`);
      if (mission) queryParts.push(`mission=${mission}`);
      if (instrument) queryParts.push(`instrument=${instrument}`);
      if (date) queryParts.push(`date=${date}`);
      if (limit !== 5) queryParts.push(`limit=${limit}`);
      if (offset !== 0) queryParts.push(`offset=${offset}`);
    } else if (endpoint === '/public/spectra') {
      if (observationId) queryParts.push(`observation_id=${observationId}`);
      if (date) queryParts.push(`date=${date}`);
      if (mission) queryParts.push(`mission=${mission}`);
      if (downsample) queryParts.push(`downsample=true`);
      if (downsample && zoomLevel !== 0) queryParts.push(`zoom_level=${zoomLevel}`);
      if (targetWavelengths) queryParts.push(`target_wavelengths=${targetWavelengths}`);
      if (limit !== 5) queryParts.push(`limit=${limit}`);
      if (offset !== 0) queryParts.push(`offset=${offset}`);
    } else if (endpoint === '/public/spectra/{id}') {
      url = `http://localhost:8000/api/v1/public/spectra/${measurementId}`;
      if (downsample) queryParts.push(`downsample=true`);
      if (downsample && zoomLevel !== 0) queryParts.push(`zoom_level=${zoomLevel}`);
      if (targetWavelengths) queryParts.push(`target_wavelengths=${targetWavelengths}`);
    }

    if (queryParts.length > 0) {
      url += `?${queryParts.join('&')}`;
    }

    return `curl -H "X-API-Key: ${apiKey || 'YOUR_API_KEY'}" \\\n     "${url}"`;
  }, [endpoint, apiKey, mission, instrument, targetName, date, observationId, measurementId, limit, offset, downsample, zoomLevel, targetWavelengths]);

  // Pre-fill valid database records automatically for testing
  const autoFillSample = () => {
    setMission('CH3');
    setInstrument('LIBS');
    setTargetName('Moon');
    setDate('2023-08-25');
    setObservationId('LIB-20230825-145453-00');
    setMeasurementId('FI-20230825-145453-00-1');
    setLimit(5);
    setOffset(0);
    setDownsample(true);
    setZoomLevel(1);
    setTargetWavelengths('393.37,396.15');
  };

  const handleSend = async () => {
    setLoading(true);
    setResponse(null);
    setError(null);
    try {
      let data: any;
      if (endpoint === '/public/missions') {
        data = await apiService.fetchPublicMissions(apiKey, limit, offset);
      } else if (endpoint === '/public/missions/{code}') {
        if (!mission) throw new Error('Mission code parameter is required');
        data = await apiService.fetchPublicMissionByCode(apiKey, mission);
      } else if (endpoint === '/public/instruments') {
        data = await apiService.fetchPublicInstruments(apiKey, mission || undefined);
      } else if (endpoint === '/public/observations') {
        data = await apiService.fetchPublicObservations(apiKey, {
          mission: mission || undefined,
          instrument: instrument || undefined,
          targetName: targetName || undefined,
          date: date || undefined,
          limit,
          offset
        });
      } else if (endpoint === '/public/measurements') {
        data = await apiService.fetchPublicMeasurements(apiKey, {
          observationId: observationId || undefined,
          mission: mission || undefined,
          instrument: instrument || undefined,
          date: date || undefined,
          limit,
          offset
        });
      } else if (endpoint === '/public/spectra') {
        data = await apiService.fetchPublicBulkSpectra(apiKey, {
          observationId: observationId || undefined,
          date: date || undefined,
          mission: mission || undefined,
          downsample,
          zoomLevel,
          targetWavelengths: targetWavelengths || undefined,
          limit,
          offset
        });
      } else if (endpoint === '/public/spectra/{id}') {
        if (!measurementId) {
          throw new Error('Measurement ID is required');
        }
        data = await apiService.fetchPublicSpectrum(apiKey, measurementId, {
          downsample,
          zoomLevel,
          targetWavelengths: targetWavelengths || undefined
        });
      }
      setResponse(data);
    } catch (err: any) {
      setError(err.message || 'An error occurred during request execution.');
    } finally {
      setLoading(false);
    }
  };

  const copyResponseToClipboard = () => {
    const content = response ? JSON.stringify(response, null, 2) : error || '';
    if (!content) return;
    navigator.clipboard.writeText(content).then(() => {
      setCopyStatus('copied');
      setTimeout(() => setCopyStatus('copy'), 2000);
    });
  };

  return (
    <div className="bg-white dark:bg-[#0f0f11] border border-neutral-200 dark:border-neutral-800 rounded-xl p-6 shadow-sm">
      <div className="flex items-center justify-between mb-5 border-b border-neutral-200 dark:border-neutral-800 pb-3">
        <div className="text-[12px] font-bold text-neutral-800 dark:text-[#f0f0f0] tracking-wider uppercase">
          Interactive Console
        </div>
        <button 
          onClick={autoFillSample}
          className="px-3 py-1.5 border border-neutral-300 dark:border-neutral-800 text-neutral-800 dark:text-neutral-300 hover:text-neutral-900 dark:hover:text-white hover:border-neutral-400 dark:hover:border-neutral-600 bg-transparent text-[9px] font-bold uppercase tracking-wider rounded-lg cursor-pointer transition-all duration-150"
        >
          Auto-fill Sample Data
        </button>
      </div>
      
      {/* Endpoint Selector */}
      <div className="space-y-4 mb-5">
        <div>
          <label className="block text-[9.5px] font-bold uppercase tracking-wider text-neutral-800 dark:text-neutral-300 mb-2">Select Endpoint Route</label>
          <select
            className="w-full text-[12px] bg-canvas dark:bg-[#18181d] border border-neutral-300 dark:border-neutral-800 px-3.5 py-2.5 text-neutral-900 dark:text-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-700 cursor-pointer"
            value={endpoint}
            style={{ colorScheme: 'dark' }}
            onChange={(e) => {
              setEndpoint(e.target.value);
              setResponse(null);
              setError(null);
            }}
          >
            <option value="/public/missions">GET /public/missions</option>
            <option value="/public/missions/{code}">GET /public/missions/{"{code}"}</option>
            <option value="/public/instruments">GET /public/instruments</option>
            <option value="/public/observations">GET /public/observations</option>
            <option value="/public/measurements">GET /public/measurements</option>
            <option value="/public/spectra">GET /public/spectra (Bulk)</option>
            <option value="/public/spectra/{id}">GET /public/spectra/{"{id}"}</option>
          </select>
        </div>
      </div>

      {/* Dynamic Parameters block */}
      <div className="border-t border-neutral-200 dark:border-neutral-800 pt-5 mb-5">
        <div className="text-[9.5px] font-bold text-neutral-800 dark:text-neutral-300 mb-4 uppercase tracking-wider">Configure Query Parameters</div>
        <div className="space-y-4">
          
          {endpoint === '/public/missions/{code}' && (
            <div>
              <label className="block text-[10px] text-neutral-800 dark:text-neutral-300 mb-1.5 font-semibold">Mission Code (Path)</label>
              <input
                type="text"
                className="w-full text-[12px] bg-canvas dark:bg-[#18181d] border border-neutral-300 dark:border-neutral-800 px-3.5 py-2 text-neutral-900 dark:text-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-700 transition-all font-sans"
                value={mission}
                onChange={(e) => setMission(e.target.value)}
                placeholder="e.g. CH3"
              />
            </div>
          )}

          {(endpoint === '/public/missions' || endpoint === '/public/observations' || endpoint === '/public/measurements' || endpoint === '/public/spectra') && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[10px] text-neutral-800 dark:text-neutral-300 mb-1.5 font-semibold">Limit</label>
                <input
                  type="number"
                  className="w-full text-[12px] bg-canvas dark:bg-[#18181d] border border-neutral-300 dark:border-neutral-800 px-3.5 py-2 text-neutral-900 dark:text-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-700 transition-all font-sans"
                  value={limit}
                  onChange={(e) => setLimit(parseInt(e.target.value) || 0)}
                />
              </div>
              <div>
                <label className="block text-[10px] text-neutral-800 dark:text-neutral-300 mb-1.5 font-semibold">Offset</label>
                <input
                  type="number"
                  className="w-full text-[12px] bg-canvas dark:bg-[#18181d] border border-neutral-300 dark:border-neutral-800 px-3.5 py-2 text-neutral-900 dark:text-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-700 transition-all font-sans"
                  value={offset}
                  onChange={(e) => setOffset(parseInt(e.target.value) || 0)}
                />
              </div>
            </div>
          )}

          {(endpoint === '/public/instruments' || endpoint === '/public/observations') && (
            <div>
              <label className="block text-[10px] text-neutral-800 dark:text-neutral-300 mb-1.5 font-semibold">Mission Code Filter</label>
              <input
                type="text"
                className="w-full text-[12px] bg-canvas dark:bg-[#18181d] border border-neutral-300 dark:border-neutral-800 px-3.5 py-2.5 text-neutral-900 dark:text-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-700 transition-all font-sans"
                value={mission}
                onChange={(e) => setMission(e.target.value)}
                placeholder="e.g. CH3"
              />
            </div>
          )}

          {endpoint === '/public/observations' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] text-neutral-800 dark:text-neutral-300 mb-1.5 font-semibold">Instrument</label>
                  <input
                    type="text"
                    className="w-full text-[12px] bg-canvas dark:bg-[#18181d] border border-neutral-300 dark:border-neutral-800 px-3.5 py-2 text-neutral-900 dark:text-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-700 transition-all font-sans"
                    value={instrument}
                    onChange={(e) => setInstrument(e.target.value)}
                    placeholder="e.g. LIBS"
                  />
                </div>
                <div>
                  <label className="block text-[10px] text-neutral-800 dark:text-neutral-300 mb-1.5 font-semibold">Target Body</label>
                  <input
                    type="text"
                    className="w-full text-[12px] bg-canvas dark:bg-[#18181d] border border-neutral-300 dark:border-neutral-800 px-3.5 py-2 text-neutral-900 dark:text-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-700 transition-all font-sans"
                    value={targetName}
                    onChange={(e) => setTargetName(e.target.value)}
                  />
                </div>
              </div>
              <div>
                <label className="block text-[10px] text-neutral-800 dark:text-neutral-300 mb-1.5 font-semibold">Capture Date (YYYY-MM-DD)</label>
                <input
                  type="text"
                  className="w-full text-[12px] bg-canvas dark:bg-[#18181d] border border-neutral-300 dark:border-neutral-800 px-3.5 py-2.5 text-neutral-900 dark:text-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-700 transition-all font-mono"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  placeholder="e.g. 2023-08-25"
                />
              </div>
            </div>
          )}

          {endpoint === '/public/measurements' && (
            <div className="space-y-4">
              <div>
                <label className="block text-[10px] text-neutral-800 dark:text-neutral-300 mb-1.5 font-semibold">Observation / File ID</label>
                <input
                  type="text"
                  className="w-full text-[12px] bg-canvas dark:bg-[#18181d] border border-neutral-300 dark:border-neutral-800 px-3.5 py-2.5 text-neutral-900 dark:text-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-700 transition-all font-mono"
                  value={observationId}
                  onChange={(e) => setObservationId(e.target.value)}
                  placeholder="LIB-20230825-145453-00"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] text-neutral-800 dark:text-neutral-300 mb-1.5 font-semibold">Mission Filter</label>
                  <input
                    type="text"
                    className="w-full text-[12px] bg-canvas dark:bg-[#18181d] border border-neutral-300 dark:border-neutral-800 px-3.5 py-2 text-neutral-900 dark:text-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-700 transition-all font-sans"
                    value={mission}
                    onChange={(e) => setMission(e.target.value)}
                    placeholder="e.g. CH3"
                  />
                </div>
                <div>
                  <label className="block text-[10px] text-neutral-800 dark:text-neutral-300 mb-1.5 font-semibold">Instrument Filter</label>
                  <input
                    type="text"
                    className="w-full text-[12px] bg-canvas dark:bg-[#18181d] border border-neutral-300 dark:border-neutral-800 px-3.5 py-2 text-neutral-900 dark:text-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-700 transition-all font-sans"
                    value={instrument}
                    onChange={(e) => setInstrument(e.target.value)}
                    placeholder="e.g. LIBS"
                  />
                </div>
              </div>
              <div>
                <label className="block text-[10px] text-neutral-800 dark:text-neutral-300 mb-1.5 font-semibold">Capture Date (YYYY-MM-DD)</label>
                <input
                  type="text"
                  className="w-full text-[12px] bg-canvas dark:bg-[#18181d] border border-neutral-300 dark:border-neutral-800 px-3.5 py-2.5 text-neutral-900 dark:text-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-700 transition-all font-mono"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  placeholder="e.g. 2023-08-25"
                />
              </div>
            </div>
          )}

          {endpoint === '/public/spectra' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] text-neutral-800 dark:text-neutral-300 mb-1.5 font-semibold">Observation ID</label>
                  <input
                    type="text"
                    className="w-full text-[12px] bg-canvas dark:bg-[#18181d] border border-neutral-300 dark:border-neutral-800 px-3.5 py-2.5 text-neutral-900 dark:text-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-700 transition-all font-mono"
                    value={observationId}
                    onChange={(e) => setObservationId(e.target.value)}
                    placeholder="LIB-20230825-145453-00"
                  />
                </div>
                <div>
                  <label className="block text-[10px] text-neutral-800 dark:text-neutral-300 mb-1.5 font-semibold">Mission Filter</label>
                  <input
                    type="text"
                    className="w-full text-[12px] bg-canvas dark:bg-[#18181d] border border-neutral-300 dark:border-neutral-800 px-3.5 py-2 text-neutral-900 dark:text-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-700 transition-all font-sans"
                    value={mission}
                    onChange={(e) => setMission(e.target.value)}
                    placeholder="e.g. CH3"
                  />
                </div>
              </div>
              <div>
                <label className="block text-[10px] text-neutral-800 dark:text-neutral-300 mb-1.5 font-semibold">Date Filter (YYYY-MM-DD)</label>
                <input
                  type="text"
                  className="w-full text-[12px] bg-canvas dark:bg-[#18181d] border border-neutral-300 dark:border-neutral-800 px-3.5 py-2.5 text-neutral-900 dark:text-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-700 transition-all font-mono"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  placeholder="e.g. 2023-08-25"
                />
              </div>
              <div className="flex items-center gap-2 py-1">
                <input
                  type="checkbox"
                  id="downsample_bulk"
                  checked={downsample}
                  onChange={(e) => setDownsample(e.target.checked)}
                  className="rounded border-neutral-300 dark:border-neutral-800 text-neutral-900 focus:ring-neutral-400 h-4 w-4"
                />
                <label htmlFor="downsample_bulk" className="text-[12px] text-neutral-800 dark:text-neutral-300 cursor-pointer select-none">Enable LTTB Downsampling</label>
              </div>
              {downsample && (
                <div className="grid grid-cols-2 gap-3 border-l-2 border-neutral-300 dark:border-l-neutral-700 pl-3">
                  <div>
                    <label className="block text-[10px] text-neutral-800 dark:text-neutral-300 mb-1.5 font-semibold">Zoom (0-5)</label>
                    <input
                      type="number"
                      className="w-full text-[12px] bg-canvas dark:bg-[#18181d] border border-neutral-300 dark:border-neutral-800 px-3.5 py-2 text-neutral-900 dark:text-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-700 transition-all font-sans"
                      value={zoomLevel}
                      min={0}
                      max={5}
                      onChange={(e) => setZoomLevel(parseInt(e.target.value) || 0)}
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] text-neutral-800 dark:text-neutral-300 mb-1.5 font-semibold">Keep Peaks</label>
                    <input
                      type="text"
                      className="w-full text-[12px] bg-canvas dark:bg-[#18181d] border border-neutral-300 dark:border-neutral-800 px-3.5 py-2 text-neutral-900 dark:text-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-700 transition-all font-sans"
                      value={targetWavelengths}
                      placeholder="393.37"
                      onChange={(e) => setTargetWavelengths(e.target.value)}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {endpoint === '/public/spectra/{id}' && (
            <div className="space-y-4">
              <div>
                <label className="block text-[10px] text-neutral-800 dark:text-neutral-300 mb-1.5 font-semibold">Measurement ID (Path)</label>
                <input
                  type="text"
                  className="w-full text-[12px] bg-canvas dark:bg-[#18181d] border border-neutral-300 dark:border-neutral-800 px-3.5 py-2.5 text-neutral-900 dark:text-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-700 transition-all font-mono"
                  value={measurementId}
                  onChange={(e) => setMeasurementId(e.target.value)}
                  placeholder="e.g. FI-20230825-145453-00-1"
                />
              </div>
              <div className="flex items-center gap-2 py-1">
                <input
                  type="checkbox"
                  id="downsample_detail"
                  checked={downsample}
                  onChange={(e) => setDownsample(e.target.checked)}
                  className="rounded border-neutral-300 dark:border-neutral-800 text-neutral-900 focus:ring-neutral-400 h-4 w-4"
                />
                <label htmlFor="downsample_detail" className="text-[12px] text-neutral-800 dark:text-neutral-300 cursor-pointer select-none">Enable LTTB Downsampling</label>
              </div>
              {downsample && (
                <div className="grid grid-cols-2 gap-3 border-l-2 border-neutral-300 dark:border-l-neutral-700 pl-3">
                  <div>
                    <label className="block text-[10px] text-neutral-800 dark:text-neutral-300 mb-1.5 font-semibold">Zoom (0-5)</label>
                    <input
                      type="number"
                      className="w-full text-[12px] bg-canvas dark:bg-[#18181d] border border-neutral-300 dark:border-neutral-800 px-3.5 py-2.5 text-neutral-900 dark:text-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-700 transition-all font-sans"
                      value={zoomLevel}
                      min={0}
                      max={5}
                      onChange={(e) => setZoomLevel(parseInt(e.target.value) || 0)}
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] text-neutral-800 dark:text-neutral-300 mb-1.5 font-semibold">Keep Peaks</label>
                    <input
                      type="text"
                      className="w-full text-[12px] bg-canvas dark:bg-[#18181d] border border-neutral-300 dark:border-neutral-800 px-3.5 py-2.5 text-neutral-900 dark:text-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-700 transition-all font-sans"
                      value={targetWavelengths}
                      placeholder="393.37"
                      onChange={(e) => setTargetWavelengths(e.target.value)}
                    />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Live cURL preview box */}
      <div className="mb-5">
        <label className="block text-[9.5px] font-bold uppercase tracking-wider text-neutral-800 dark:text-neutral-300 mb-2">Live cURL Command preview</label>
        <pre className="bg-neutral-50 dark:bg-[#0f0f12] border border-neutral-200 dark:border-neutral-800 px-4 py-3 rounded-lg font-mono text-[11px] text-neutral-800 dark:text-neutral-300 overflow-x-auto whitespace-pre-wrap break-all leading-[1.6]">
          {liveCurlCommand}
        </pre>
      </div>

      <button
        onClick={handleSend}
        disabled={loading}
        className="w-full py-3 text-[10px] font-bold tracking-widest text-white dark:text-neutral-950 bg-neutral-900 hover:bg-neutral-800 dark:bg-white dark:hover:bg-neutral-100 rounded-lg uppercase transition-all duration-150 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed active:scale-95 shadow-sm border-0 flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <svg className="animate-spin h-3.5 w-3.5 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Executing Request...
          </>
        ) : 'Send Request'}
      </button>

      {/* API Console Screen */}
      {(response || error) && (
        <div className="mt-5 border-t border-neutral-200 dark:border-neutral-800 pt-4">
          <div className="flex justify-between items-center mb-3">
            <span className="text-[9.5px] font-bold uppercase tracking-wider text-neutral-800 dark:text-neutral-300">Response body</span>
            <div className="flex gap-2">
              <button 
                onClick={copyResponseToClipboard}
                className="text-[9.5px] px-2.5 py-1 border border-neutral-300 dark:border-neutral-800 text-neutral-800 dark:text-neutral-300 hover:text-neutral-900 dark:hover:text-white hover:border-neutral-400 dark:hover:border-neutral-600 bg-transparent uppercase tracking-wider rounded cursor-pointer transition-all duration-150 font-bold"
              >
                {copyStatus === 'copied' ? 'Copied' : 'Copy'}
              </button>
              {response && (
                <span className="text-[9.5px] font-mono font-bold text-neutral-800 dark:text-neutral-200 bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 px-2 py-0.5 rounded uppercase tracking-wide">
                  HTTP 200 OK
                </span>
              )}
              {error && (
                <span className="text-[9.5px] font-mono font-bold text-red-600 bg-red-50 dark:bg-red-950/40 dark:text-red-400 border border-red-200 dark:border-red-900 px-2 py-0.5 rounded uppercase tracking-wide">
                  HTTP ERROR
                </span>
              )}
            </div>
          </div>
          <div className="max-h-[250px] overflow-auto bg-neutral-50 dark:bg-[#0f0f12] text-neutral-800 dark:text-neutral-300 font-mono text-[11px] p-4 rounded-lg border border-neutral-200 dark:border-neutral-800 leading-[1.6] whitespace-pre scrollbar-thin">
            {error && <span className="text-red-600 dark:text-red-400 font-semibold">{error}</span>}
            {response && JSON.stringify(response, null, 2)}
          </div>
        </div>
      )}
    </div>
  );
}
