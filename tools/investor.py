"""
title: Level Investor
author: Level VC
author_url: https://levelvc.com
version: 1.1.0
description: Allows the agent to retrieve information about companies (public and private market), our portfolio, relevant people, and other topics of investments

Configuration:
- Configure the API key through the Open WebUI tool configuration interface
"""

import requests
from pydantic import BaseModel, Field


async def _emit_event(
    event_emitter, event_type: str, description: str, done: bool = False
):
    """Helper function to safely emit events."""
    if event_emitter:
        try:
            await event_emitter(
                {
                    "type": event_type,
                    "data": {"description": description, "done": done, "hidden": False},
                }
            )
        except Exception:
            pass


async def _emit_citation(
    event_emitter, content: str, title: str, url: str
):
    """Helper function to emit citations."""
    if event_emitter:
        try:
            await event_emitter({
                "type": "citation",
                "data": {
                    "document": [content],
                    "source": {"name": title, "url": url}
                }
            })
        except Exception:
            # Silently ignore citation emission errors to not break the tool
            pass


def _make_api_request(
    method: str, endpoint: str, data: dict = None, valves=None
) -> dict:
    """Make authenticated API request to LVC API."""
    url = f"https://api.lvcdev.com{endpoint}"
    headers = {
        "Authorization": f"Bearer {valves.api_key}",
        "Content-Type": "application/json",
    }

    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            return {"error": f"Unsupported HTTP method: {method}"}

        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}


class Tools:
    def __init__(self):
        """Initialize the Tool."""
        self.valves = self.Valves()
        self.citation = False

    class Valves(BaseModel):
        api_key: str = Field("", description="Your Level VC API key")

    async def semantic_search_transcripts(
        self,
        query: str,
        search_type: str = "balanced",
        limit: str = "30",
        symbol: str = None,
        year: str = None,
        quarter: str = None,
        min_year: str = None,
        max_year: str = None,
        extract_quotes: bool = True,
        __event_emitter__=None,
    ) -> str:
        """
        Find earnings-call transcript passages semantically related to an idea or topic.

        Use when:
          - You want concept-level matches (not just exact keywords).
          - You’re researching themes (pricing, unit economics, guidance, competition) across calls.

        Inputs:
          - query: Natural-language topic or question to match against transcript content.
          - search_type: Similarity strictness. "tight"(~>0.6), "balanced"(~>0.4), "loose"(~>0.35).
          - limit: Max results (stringified int; default "30", max 50).
          - symbol/year/quarter: Optional filters to constrain to a company/period.
          - min_year/max_year: Optional year range filters.
          - extract_quotes: If True, returns only the most relevant snippets.

        Returns:
          - List[Object] where each item includes company, date, similarity score, and either
            extracted quotes or full content (when extract_quotes=False).
        """
        # Emit start event
        search_details = f"query='{query}', search_type='{search_type}', limit={limit}"
        if symbol:
            search_details += f", symbol={symbol}"
        if year:
            search_details += f", year={year}"
        if quarter:
            search_details += f", quarter={quarter}"

        await _emit_event(
            __event_emitter__,
            "status",
            f"🔍 Searching earnings transcripts with semantic search ({search_details})",
            done=False,
        )

        data = {
            "query": query,
            "search_type": search_type,
            "limit": limit,
            "symbol": symbol,
            "year": year,
            "quarter": quarter,
            "min_year": min_year,
            "max_year": max_year,
            "extract_quotes": extract_quotes,
        }

        result = _make_api_request(
            "POST", "/investor/semantic-search-transcripts", data, self.valves
        )

        # Emit completion event
        if isinstance(result, dict) and "error" in result:
            await _emit_event(
                __event_emitter__,
                "status",
                f"❌ Semantic search failed: {result.get('error', 'Unknown error')}",
                done=True,
            )
        else:
            result_count = len(result) if isinstance(result, list) else "unknown"
            await _emit_event(
                __event_emitter__,
                "status",
                f"✅ Semantic search completed - found {result_count} results",
                done=True,
            )
            
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict):
                        citation = item.get("citation", "")
                        quotes = item.get("quotes", "")
                        
                        await _emit_citation(
                            __event_emitter__,
                            content=quotes,
                            title=citation,
                            url="https://levelvc.com"
                        )

        return result

    async def keyword_search_transcripts(
        self,
        keywords: str,
        limit: str = "25",
        symbol: str = None,
        year: str = None,
        quarter: str = None,
        min_year: str = None,
        max_year: str = None,
        match_type: str = "any",
        extract_quotes: bool = True,
        __event_emitter__=None,
    ) -> str:
        """
        Search transcripts for exact keyword matches.

        Best for:
          - Pinpointing specific phrases (product names, SKUs, tickers).
          - Tracking literal mentions across calls or time periods.

        Args:
            keywords: Space-separated terms.
            limit: Max results (default "25", up to 50).
            symbol/year/quarter/min_year/max_year: Filters by company or date.
            match_type: "any" (default) or "all" for multiple keywords.
            extract_quotes: If True, returns only matching snippets.

        Returns:
            List of results with metadata and snippets or full content.
        """
        # Emit start event
        search_details = (
            f"keywords='{keywords}', match_type='{match_type}', limit={limit}"
        )
        if symbol:
            search_details += f", symbol={symbol}"
        if year:
            search_details += f", year={year}"
        if quarter:
            search_details += f", quarter={quarter}"

        await _emit_event(
            __event_emitter__,
            "status",
            f"🔍 Searching earnings transcripts with keyword search ({search_details})",
            done=False,
        )

        data = {
            "keywords": keywords,
            "limit": limit,
            "symbol": symbol,
            "year": year,
            "quarter": quarter,
            "min_year": min_year,
            "max_year": max_year,
            "match_type": match_type,
            "extract_quotes": extract_quotes,
        }

        result = _make_api_request("POST", "/investor/keyword-search-transcripts", data, self.valves)

        # Emit completion event
        if isinstance(result, dict) and "error" in result:
            await _emit_event(
                __event_emitter__,
                "status",
                f"❌ Keyword search failed: {result.get('error', 'Unknown error')}",
                done=True,
            )
        else:
            result_count = len(result) if isinstance(result, list) else "unknown"
            await _emit_event(
                __event_emitter__,
                "status",
                f"✅ Keyword search completed - found {result_count} results",
                done=True,
            )
            
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict):
                        citation = item.get("citation", "")
                        quotes = item.get("quotes", "")
                        
                        await _emit_citation(
                            __event_emitter__,
                            content=quotes,
                            title=citation,
                            url="https://levelvc.com"
                        )

        return result

    async def get_transcript_details(
        self, symbol: str, year: str, quarter: str, __event_emitter__=None
    ) -> str:
        """
        Fetch the full text for a specific earnings transcript.

        Use when:
          - You need complete context after a search hit.
          - You’re extracting long-form sections (prepared remarks, Q&A).

        Inputs:
          - symbol: Ticker (e.g., "AAPL").
          - year: Four-digit year.
          - quarter: "Q1" | "Q2" | "Q3" | "Q4".

        Returns:
          - Object containing the full transcript and associated metadata.
        """
        await _emit_event(
            __event_emitter__,
            "status",
            f"📄 Fetching transcript details for {symbol.upper()} {year} {quarter.upper()}",
            done=False,
        )

        data = {"symbol": symbol.upper(), "year": year, "quarter": quarter.upper()}

        result = _make_api_request("POST", "/investor/transcript-details", data, self.valves)

        # Emit completion event
        if isinstance(result, dict) and "error" in result:
            await _emit_event(
                __event_emitter__,
                "status",
                f"❌ Failed to fetch transcript: {result.get('error', 'Unknown error')}",
                done=True,
            )
        else:
            await _emit_event(
                __event_emitter__,
                "status",
                f"✅ Successfully fetched transcript for {symbol.upper()} {year} {quarter.upper()}",
                done=True,
            )
            
            if isinstance(result, dict):
                citation = result.get("citation", "")
                quotes = result.get("quotes", "")
                
                await _emit_citation(
                    __event_emitter__,
                    content=quotes,
                    title=citation,
                    url="https://levelvc.com"
                )

        return result

    async def semantic_search_knowledge(
        self,
        query: str,
        search_type: str = "balanced",
        limit: str = "25",
        entity_type: str = None,
        extract_quotes: bool = True,
        __event_emitter__=None,
    ) -> str:
        """
        Retrieve semantically relevant items from Level’s knowledge base.

        Use when:
          - You’re researching companies, domain groups, or documents by concept.
          - You need context that spans multiple entity types.
          - You need to validate concepts in-market by seeing if prominent authors support various concepts.

        Inputs:
          - query: Natural-language topic or question.
          - search_type: "tight" | "balanced" | "loose" (see transcript search).
          - limit: Max results (stringified int; default "25", max 50).
          - entity_type: Optional filter: "organization" | "domain_group" | "document".
          - extract_quotes: If True, returns key snippets rather than full content.

        Returns:
          - List[Object] containing entity metadata, similarity, and quotes/content.
        """
        # Emit start event
        search_details = f"query='{query}', search_type='{search_type}', limit={limit}"
        if entity_type:
            search_details += f", entity_type={entity_type}"

        await _emit_event(
            __event_emitter__,
            "status",
            f"🧠 Searching knowledge base with semantic search ({search_details})",
            done=False,
        )

        data = {
            "query": query,
            "search_type": search_type,
            "limit": limit,
            "entity_type": entity_type,
            "extract_quotes": extract_quotes,
        }

        result = _make_api_request("POST", "/investor/semantic-search-knowledge", data, self.valves)

        # Emit completion event
        if isinstance(result, dict) and "error" in result:
            await _emit_event(
                __event_emitter__,
                "status",
                f"❌ Knowledge search failed: {result.get('error', 'Unknown error')}",
                done=True,
            )
        else:
            result_count = len(result) if isinstance(result, list) else "unknown"
            await _emit_event(
                __event_emitter__,
                "status",
                f"✅ Knowledge search completed - found {result_count} results",
                done=True,
            )
            
            # Emit citations for each result
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict):
                        title = item.get("title", "Unknown")
                        url = item.get("public_url", "")
                        quotes = item.get("quotes", "")
                        
                        
                        await _emit_citation(
                            __event_emitter__,
                            content=quotes,
                            title=f"Knowledge Page {title}",
                            url=url
                        )

        return result

    async def find_similar_organizations(
        self,
        query: str,
        search_type: str = "balanced",
        limit: str = "100",
        country_code: str = None,
        funding_stage: str = None,
        level_portfolio: str = None,
        min_funding_usd: str = None,
        max_funding_usd: str = None,
        min_market_cap: str | None = None,
        max_market_cap: str | None = None,
        status: str = "Active",
        use_reference_org: bool = False,
        reference_search_method: str = "name",
        use_llm_filtering: bool = True,
        __event_emitter__=None,
    ) -> str:
        """
        Generate a ranked set of companies similar to a concept or a specific organization.

        Core use cases:
          - Prospecting: “Who looks like Company X?”
          - Market maps: “Who fits this thesis in region Y/stage Z?”
          - Quality signal overlay: use syndicated investor stats (FMM) on the returned set.
          - When you want to know a competitor set to a given company, or how dense a given
          "space" is.

        Inputs:
          - query: Concept text OR a specific org identifier (according to Level’s DB).
          - search_type: Similarity strictness ("tight" | "balanced" | "loose").
          - limit: Max results (default "100"; up to "5000" if supported).
          - country_code: 3-letter ISO (e.g., "USA", "GBR").
          - funding_stage: seed | early | growth | ipo | acquisition | crypto_exit | unknown.
          - level_portfolio: "true" to restrict to Level portfolio companies.
          - min_funding_usd / max_funding_usd: Funding range filters (stringified numbers).
          - min_market_cap / max_market_cap: Filter on the current market cap of a company.
          - status: "Active" (default) or "Not Active".
          - use_reference_org: True to anchor similarity to a specific org.
          - reference_search_method: "name" | "website" for the reference lookup.
          - use_llm_filtering: If True, applies LLM relevance filtering to the raw set.

        Returns:
          - List[Object] with org details, similarity, and syndicate augmentation:
            * syndicate_members (unique investors),
            * median_fmm_score,
            * max_fmm_score.

        Examples of usage:
        Here are some concrete use-cases you might implement with your find_similar_organizations function. I’ll frame them around practical scenarios for venture, strategy, and research workflows:

        ⸻

        1. Competitor Landscape for a Portfolio Company

        Scenario: You’re evaluating how crowded the market is around a specific portfolio company.
        find_similar_organizations(
            query="Anthropic",
            use_reference_org=True,
            reference_search_method="name",
            search_type="tight",
            limit="50",
            country_code="USA",
            status="Active",
        )

        Outcome: Returns ~50 U.S.-based active companies most similar to Anthropic, letting you map competitors, adjacent startups, or acquisition targets.

        ⸻

        2. Regional Market Map for a Thesis

        Scenario: You’re drafting a market map of fintech infra startups in Latin America.
        find_similar_organizations(
            query="fintech infrastructure",
            search_type="loose",
            country_code="BRA",
            funding_stage="early",
            limit="200",
        )

        Outcome: Produces an ecosystem-style map of early-stage fintech infra companies in Brazil, useful for thesis validation and sourcing.

        ⸻

        3. Prospecting by Funding Stage and Capital Range

        Scenario: You want to identify Series B AI companies with significant funding but below unicorn status.
        find_similar_organizations(
            query="artificial intelligence",
            funding_stage="growth",
            min_funding_usd="50000000",   # $50M
            max_funding_usd="500000000",  # $500M
            search_type="balanced",
            limit="150",
        )

        Outcome: Returns companies in the “sweet spot” funding band, prime for follow-on investment opportunities.

        ⸻

        4. Market Cap Screened Peer Group

        Scenario: Benchmarking public companies in EV battery tech by market cap range.
        find_similar_organizations(
            query="EV battery technology",
            min_market_cap="1000000000",   # $1B
            max_market_cap="10000000000",  # $10B
            funding_stage="ipo",
            status="Active",
            search_type="loose",
        )

        Outcome: Gives a peer group of public battery tech players for comparative valuation and benchmarking.

        ⸻

        5. Internal Portfolio Cross-Mapping

        Scenario: You want to know which portfolio companies resemble one another for collab or co-investor intros.
        find_similar_organizations(
            query="climate tech",
            level_portfolio="true",
            search_type="loose",
            limit="100",
        )

        Outcome: Produces clusters of Level’s own climate tech portfolio companies, useful for portfolio synergies or LP reporting.

        ⸻

        6. LLM-Filtered Theme Exploration

        Scenario: You’re exploring “agentic AI” as an emerging theme but want to filter noise out of the long tail.
        find_similar_organizations(
            query="agentic AI",
            use_llm_filtering=True,
            search_type="loose",
            limit="500",
        )

        Outcome: LLM filters the raw similarity results to remove irrelevant hits (e.g., agencies, consultancies), giving you a tighter thesis-aligned set.
        """
        # Emit start event
        search_details = f"query='{query}', search_type='{search_type}', limit={limit}"
        if country_code:
            search_details += f", country={country_code}"
        if funding_stage:
            search_details += f", stage={funding_stage}"
        if use_reference_org:
            search_details += ", reference_org=True"

        await _emit_event(
            __event_emitter__,
            "status",
            f"🏢 Finding similar organizations ({search_details})",
            done=False,
        )

        data = {
            "query": query,
            "search_type": search_type,
            "limit": limit,
            "country_code": country_code,
            "funding_stage": funding_stage,
            "level_portfolio": level_portfolio,
            "min_funding_usd": min_funding_usd,
            "max_funding_usd": max_funding_usd,
            "min_market_cap": min_market_cap,
            "max_market_cap": max_market_cap,
            "status": status,
            "use_reference_org": use_reference_org,
            "reference_search_method": reference_search_method,
            "use_llm_filtering": use_llm_filtering,
        }

        result = _make_api_request("POST", "/investor/similar-organizations", data, self.valves)

        # Emit completion event
        if isinstance(result, dict) and "error" in result:
            await _emit_event(
                __event_emitter__,
                "status",
                f"❌ Organization search failed: {result.get('error', 'Unknown error')}",
                done=True,
            )
        else:
            result_count = len(result) if isinstance(result, list) else "unknown"
            await _emit_event(
                __event_emitter__,
                "status",
                f"✅ Found {result_count} similar organizations",
                done=True,
            )

        return result

    async def get_organization_details(
        self, identifier: str, search_by: str = "uuid", __event_emitter__=None
    ) -> str:
        """
        Retrieve an organization’s complete profile (with investor syndicate quality signals).

        Use when:
          - You need a company dossier for diligence or CRM enrichment.
          - You want investor-quality context (median/max FMM) alongside basics.

        Inputs:
          - identifier: Organization UUID, canonical name, or website.
          - search_by: "uuid" | "name" | "website".

        Returns:
          - Object with comprehensive org fields (description, funding, labels, etc.) plus:
            * syndicate_members,
            * median_fmm_score,
            * max_fmm_score.
        """
        await _emit_event(
            __event_emitter__,
            "status",
            f"🏢 Fetching organization details for {identifier} (by {search_by})",
            done=False,
        )

        data = {"identifier": identifier, "search_by": search_by}

        result = _make_api_request("POST", "/investor/organization-details", data, self.valves)

        # Emit completion event
        if isinstance(result, dict) and "error" in result:
            await _emit_event(
                __event_emitter__,
                "status",
                f"❌ Failed to fetch organization details: {result.get('error', 'Unknown error')}",
                done=True,
            )
        else:
            org_name = (
                result.get("name", identifier)
                if isinstance(result, dict)
                else identifier
            )
            await _emit_event(
                __event_emitter__,
                "status",
                f"✅ Successfully fetched details for {org_name}",
                done=True,
            )

        return result

    async def search_documents(
        self,
        query: str,
        search_type: str = "balanced",
        limit: str = "25",
        author: str = None,
        tags: str = None,
        extract_quotes: bool = True,
        __event_emitter__=None,
    ) -> str:
        """
        Concept search across internal documents with optional author/tag filters.

        Use when:
          - You’re hunting for memos, notes, or writeups matching a thesis or topic.
          - You need just the key passages (quotes) rather than full text.
          - You want to validate or learn about a given topical area.

        Inputs:
          - query: Natural-language topic.
          - search_type: "tight" | "balanced" | "loose".
          - limit: Max results (stringified int; default "25", max 50).
          - author: Optional exact author filter.
          - tags: Optional comma-separated tag filter.
          - extract_quotes: If True, returns the most relevant snippets.

        Returns:
          - List[Object] with doc metadata, similarity, and quotes/full content.
        """
        # Emit start event
        search_details = f"query='{query}', search_type='{search_type}', limit={limit}"
        if author:
            search_details += f", author={author}"
        if tags:
            search_details += f", tags={tags}"

        await _emit_event(
            __event_emitter__,
            "status",
            f"📄 Searching documents ({search_details})",
            done=False,
        )

        data = {
            "query": query,
            "search_type": search_type,
            "limit": limit,
            "author": author,
            "tags": tags,
            "extract_quotes": extract_quotes,
        }

        result = _make_api_request("POST", "/investor/search-documents", data, self.valves)

        # Emit completion event
        if isinstance(result, dict) and "error" in result:
            await _emit_event(
                __event_emitter__,
                "status",
                f"❌ Document search failed: {result.get('error', 'Unknown error')}",
                done=True,
            )
        else:
            result_count = len(result) if isinstance(result, list) else "unknown"
            await _emit_event(
                __event_emitter__,
                "status",
                f"✅ Document search completed - found {result_count} documents",
                done=True,
            )

        return result

    async def list_recent_documents(
        self,
        limit: str = "50",
        author: str = None,
        tags: str = None,
        __event_emitter__=None,
    ) -> str:
        """
        Browse the most recently added or updated documents.

        Use when:
          - You want a quick pulse on what’s new.
          - You’re scanning by person or topical tag.

        Inputs:
          - limit: Max items (stringified int; default "50", max 100).
          - author: Optional exact author filter.
          - tags: Optional comma-separated tag filter.

        Returns:
          - List[Object] with recent documents and their metadata.
        """
        # Emit start event
        filter_details = f"limit={limit}"
        if author:
            filter_details += f", author={author}"
        if tags:
            filter_details += f", tags={tags}"

        await _emit_event(
            __event_emitter__,
            "status",
            f"📅 Fetching recent documents ({filter_details})",
            done=False,
        )

        data = {"limit": limit, "author": author, "tags": tags}

        result = _make_api_request("POST", "/investor/recent-documents", data, self.valves)

        # Emit completion event
        if isinstance(result, dict) and "error" in result:
            await _emit_event(
                __event_emitter__,
                "status",
                f"❌ Failed to fetch recent documents: {result.get('error', 'Unknown error')}",
                done=True,
            )
        else:
            doc_count = len(result) if isinstance(result, list) else "unknown"
            await _emit_event(
                __event_emitter__,
                "status",
                f"✅ Successfully fetched {doc_count} recent documents",
                done=True,
            )

        return result

    async def keyword_search_knowledge(
        self,
        keywords: str,
        limit: str = "25",
        entity_type: str = None,
        match_type: str = "any",
        extract_quotes: bool = True,
        __event_emitter__=None,
    ) -> str:
        """
        Keyword-based (exact match) search in the knowledge base.

        Best for:
          - Finding literal terms (codes, acronyms, exact phrases).
          - Combining multiple specific keywords.

        Args:
            keywords: Space-separated terms.
            limit: Max results (default "25", up to 50).
            entity_type: "organization", "domain_group", or "document".
            match_type: "any" or "all".
            extract_quotes: Return snippets if True.

        Returns:
            List of entities/documents with metadata and snippets/full content.
        """
        # Emit start event
        search_details = (
            f"keywords='{keywords}', match_type='{match_type}', limit={limit}"
        )
        if entity_type:
            search_details += f", entity_type={entity_type}"

        await _emit_event(
            __event_emitter__,
            "status",
            f"🔍 Searching knowledge base with keywords ({search_details})",
            done=False,
        )

        data = {
            "keywords": keywords,
            "limit": limit,
            "entity_type": entity_type,
            "match_type": match_type,
            "extract_quotes": extract_quotes,
        }

        result = _make_api_request("POST", "/investor/keyword-search-knowledge", data, self.valves)

        # Emit completion event
        if isinstance(result, dict) and "error" in result:
            await _emit_event(
                __event_emitter__,
                "status",
                f"❌ Knowledge keyword search failed: {result.get('error', 'Unknown error')}",
                done=True,
            )
        else:
            result_count = len(result) if isinstance(result, list) else "unknown"
            await _emit_event(
                __event_emitter__,
                "status",
                f"✅ Knowledge keyword search completed - found {result_count} results",
                done=True,
            )
            
            # Emit citations for each result
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict):
                        title = item.get("title", "Unknown")
                        url = item.get("public_url", "")
                        quotes = item.get("quotes", "")
                        
                        await _emit_citation(
                            __event_emitter__,
                            content=quotes,
                            title=f"Knowledge Page {title}",
                            url=url
                        )

        return result

    async def fetch_knowledge_page(self, uuid: str, __event_emitter__=None) -> str:
        """
        Get the full content of a specific knowledge page by UUID.

        Use when:
          - You need to display or analyze a single page after finding it via search.

        Inputs:
          - uuid: Knowledge page UUID.

        Returns:
          - Object with the page title, content, and metadata.
        """

        await _emit_event(
            __event_emitter__,
            "status",
            f"📃 Fetching knowledge page {uuid}",
            done=False,
        )

        data = {"uuid": uuid}

        result = _make_api_request("POST", "/investor/fetch-knowledge-page", data, self.valves)

        # Emit completion event
        if isinstance(result, dict) and "error" in result:
            await _emit_event(
                __event_emitter__,
                "status",
                f"❌ Failed to fetch knowledge page: {result.get('error', 'Unknown error')}",
                done=True,
            )
        else:
            page_title = result.get("title", uuid) if isinstance(result, dict) else uuid
            await _emit_event(
                __event_emitter__,
                "status",
                f"✅ Successfully fetched knowledge page: {page_title}",
                done=True,
            )
            
            if isinstance(result, dict):
                title = result.get("title", "Unknown")
                url = result.get("public_url", "")
                quotes = result.get("quotes", "")
                
                
                await _emit_citation(
                    __event_emitter__,
                    content=quotes,
                    title=f"Knowledge Page {title}",
                    url=url
                )

        return result

    async def get_document_details(self, uuid: str, __event_emitter__=None) -> str:
        """
        Get complete details of a specific document.

        Best for:
          - Deep analysis after a document search hit.
          - Retrieving download link or rendering full text.

        Args:
            uuid: Document UUID.

        Returns:
            Object with metadata, content, and download link.
        """
        await _emit_event(
            __event_emitter__,
            "status",
            f"📄 Fetching document details for {uuid}",
            done=False,
        )

        data = {"uuid": uuid}

        result = _make_api_request("POST", "/investor/document-details", data, self.valves)

        # Emit completion event
        if isinstance(result, dict) and "error" in result:
            await _emit_event(
                __event_emitter__,
                "status",
                f"❌ Failed to fetch document details: {result.get('error', 'Unknown error')}",
                done=True,
            )
        else:
            doc_title = result.get("title", uuid) if isinstance(result, dict) else uuid
            await _emit_event(
                __event_emitter__,
                "status",
                f"✅ Successfully fetched document: {doc_title}",
                done=True,
            )

        return result
