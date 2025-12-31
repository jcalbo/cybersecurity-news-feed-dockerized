#!/usr/bin/env python3
"""
REST API Server with Elasticsearch caching for Streamlit frontend.
"""
import os
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# Import MCP server functions
from mcp_server import (
    _fetch_all_feeds,
    _filter_by_time,
    _filter_by_search,
    _filter_by_sources,
    _format_json,
    _format_markdown,
    RSS_FEEDS,
)

# Import Elasticsearch client
from elasticsearch_client import get_elasticsearch_client

# Configuration
ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "localhost")
ELASTICSEARCH_PORT = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
CACHE_DURATION_MINUTES = int(os.getenv("CACHE_DURATION_MINUTES", "10"))

# Create FastAPI app
app = FastAPI(
    title="Cybersecurity News API",
    description="REST API for cybersecurity news aggregation with Elasticsearch caching",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Elasticsearch client
es_client = None


def _should_refresh_cache() -> bool:
    """Check if cache should be refreshed based on last fetch time."""
    if es_client is None:
        return True
    
    latest_fetch = es_client.get_latest_fetch_time()
    
    if latest_fetch is None:
        return True
    
    time_since_fetch = datetime.now() - latest_fetch.replace(tzinfo=None)
    cache_duration = timedelta(minutes=CACHE_DURATION_MINUTES)
    
    return time_since_fetch >= cache_duration


# Request models
class GetNewsRequest(BaseModel):
    hours: Optional[int] = 24
    sources: Optional[List[str]] = None
    search: Optional[str] = None
    response_format: str = "json"
    force_refresh: bool = False


class ListSourcesRequest(BaseModel):
    response_format: str = "json"


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize Elasticsearch on startup."""
    global es_client
    
    print("🚀 Initializing Elasticsearch connection...")
    print(f"📊 Elasticsearch: {ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}")
    print(f"⏱️  Cache duration: {CACHE_DURATION_MINUTES} minutes")
    
    try:
        es_client = get_elasticsearch_client(ELASTICSEARCH_HOST, ELASTICSEARCH_PORT)
        if es_client.health_check():
            print("✅ Elasticsearch connection successful")
            doc_count = es_client.count_documents()
            print(f"📚 Current documents in index: {doc_count}")
        else:
            print("⚠️  Elasticsearch health check failed - will retry on first request")
    except Exception as e:
        print(f"⚠️  Could not connect to Elasticsearch: {e}")
        print("⚠️  Server will start but caching will not work until Elasticsearch is available")


# REST API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Cybersecurity News API",
        "version": "1.0.0",
        "elasticsearch": {
            "host": f"{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}",
            "cache_duration_minutes": CACHE_DURATION_MINUTES,
            "connected": es_client is not None and es_client.health_check()
        },
        "endpoints": {
            "health": "/health",
            "elasticsearch_health": "/health/elasticsearch",
            "get_news": "/api/news",
            "list_sources": "/api/sources",
            "elasticsearch_stats": "/api/stats"
        }
    }


@app.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "healthy", "service": "cybersecurity_news_api"}


@app.get("/health/elasticsearch")
async def elasticsearch_health():
    """Elasticsearch-specific health check."""
    if es_client is None:
        raise HTTPException(status_code=503, detail="Elasticsearch client not initialized")
    
    try:
        is_healthy = es_client.health_check()
        doc_count = es_client.count_documents()
        latest_fetch = es_client.get_latest_fetch_time()
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "elasticsearch": f"{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}",
            "connected": is_healthy,
            "total_documents": doc_count,
            "latest_fetch": latest_fetch.isoformat() if latest_fetch else None,
            "cache_duration_minutes": CACHE_DURATION_MINUTES
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Elasticsearch error: {str(e)}")


@app.post("/api/news")
async def get_news(request: GetNewsRequest):
    """Get cybersecurity news with Elasticsearch caching."""
    try:
        # Check if we need to refresh from RSS feeds
        should_refresh = request.force_refresh or _should_refresh_cache()
        
        if should_refresh:
            print("🔄 Fetching fresh news from RSS feeds...")
            # Fetch from RSS feeds
            news_items = await _fetch_all_feeds()
            
            # Store in Elasticsearch
            if es_client and news_items:
                success, failed = es_client.bulk_store_news(news_items)
                print(f"📦 Stored {success} items in Elasticsearch ({failed} failed)")
        
        # Retrieve from Elasticsearch with filters
        if es_client:
            print(f"📖 Retrieving from Elasticsearch (hours={request.hours}, sources={request.sources}, search={request.search})")
            filtered_news = es_client.get_news(
                hours=request.hours,
                sources=request.sources,
                search=request.search,
                size=100
            )
        else:
            # Fallback: fetch and filter directly
            print("⚠️  Elasticsearch unavailable - fetching directly from RSS feeds")
            news_items = await _fetch_all_feeds()
            filtered_news = _filter_by_time(news_items, request.hours)
            filtered_news = _filter_by_search(filtered_news, request.search)
            filtered_news = _filter_by_sources(filtered_news, request.sources)
        
        # Sort by publication date (newest first)
        filtered_news = sorted(filtered_news, key=lambda x: x["published"], reverse=True)
        
        # Format response
        if request.response_format == "markdown":
            return {"content": _format_markdown(filtered_news)}
        else:
            import json
            return json.loads(_format_json(filtered_news))
            
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/sources")
async def list_sources():
    """List all available news sources."""
    try:
        sources = [
            {"name": name, "feed_url": url}
            for name, url in RSS_FEEDS.items()
        ]
        return {
            "total_sources": len(sources),
            "sources": sources
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/stats")
async def elasticsearch_stats():
    """Get Elasticsearch statistics."""
    if es_client is None:
        return {"error": "Elasticsearch not connected"}
    
    try:
        total_docs = es_client.count_documents()
        latest_fetch = es_client.get_latest_fetch_time()
        
        return {
            "total_documents": total_docs,
            "latest_fetch": latest_fetch.isoformat() if latest_fetch else None,
            "index_name": es_client.index_name,
            "elasticsearch_host": f"{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}",
            "cache_duration_minutes": CACHE_DURATION_MINUTES,
            "cache_is_fresh": not _should_refresh_cache()
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print("🚀 Starting Cybersecurity News API Server...")
    print("📡 REST API: http://0.0.0.0:8000")
    print("📰 Endpoints:")
    print("  - GET  /health")
    print("  - GET  /health/elasticsearch")
    print("  - POST /api/news")
    print("  - GET  /api/sources")
    print("  - GET  /api/stats")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
