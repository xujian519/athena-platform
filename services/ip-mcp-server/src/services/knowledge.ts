/**
 * 知识库服务模块
 * 使用Qdrant进行向量检索，Neo4j进行关系查询
 */

import { QdrantClient } from "@qdrant/js-client-rest";
import neo4j from "neo4j-driver";
import type {
  KnowledgeEntry,
  LegalProvision,
  SearchResult,
} from "../types/index.js";
import logger from "../utils/logger.js";

const QDRANT_URL = process.env.QDRANT_URL || "http://localhost:6333";
const QDRANT_COLLECTION = process.env.QDRANT_COLLECTION || "ip_knowledge";
const NEO4J_URI = process.env.NEO4J_URI || "bolt://localhost:7687";
const NEO4J_USER = process.env.NEO4J_USER || "neo4j";
const NEO4J_PASSWORD = process.env.NEO4J_PASSWORD || "password";

const qdrantClient = new QdrantClient({ url: QDRANT_URL });
const neo4jDriver = neo4j.driver(
  NEO4J_URI,
  neo4j.auth.basic(NEO4J_USER, NEO4J_PASSWORD),
);

/**
 * 向量相似度检索
 */
export async function vectorSearch(
  queryVector: number[],
  limit: number = 10,
  scoreThreshold: number = 0.7,
): Promise<SearchResult[]> {
  logger.info("Performing vector search", { limit, scoreThreshold });

  try {
    const results = await qdrantClient.search(QDRANT_COLLECTION, {
      vector: queryVector,
      limit,
      score_threshold: scoreThreshold,
    });

    return results.map((result) => ({
      patentNumber: (result.payload?.patentNumber as string) || "",
      title: (result.payload?.title as string) || "",
      abstract: (result.payload?.abstract as string) || "",
      applicant: (result.payload?.applicant as string) || "",
      filingDate: (result.payload?.filingDate as string) || "",
      publicationDate: (result.payload?.publicationDate as string) || "",
      similarityScore: result.score || 0,
      legalStatus: result.payload?.legalStatus as string | undefined,
    }));
  } catch (error) {
    logger.error("Vector search failed", { error });
    throw new Error(
      `向量检索失败: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}

/**
 * 查询知识库条目
 */
export async function queryKnowledge(
  queryVector: number[],
  type?: KnowledgeEntry["type"],
  limit: number = 5,
): Promise<KnowledgeEntry[]> {
  logger.info("Querying knowledge base", { type, limit });

  try {
    const filter = type
      ? {
          must: [
            {
              key: "type",
              match: { value: type },
            },
          ],
        }
      : undefined;

    const results = await qdrantClient.search(QDRANT_COLLECTION, {
      vector: queryVector,
      limit,
      filter,
    });

    return results.map((result) => ({
      id: result.id as string,
      title: (result.payload?.title as string) || "",
      content: (result.payload?.content as string) || "",
      type: (result.payload?.type as KnowledgeEntry["type"]) || "technical",
      metadata: (result.payload?.metadata as Record<string, unknown>) || {},
      embedding: result.vector as number[],
    }));
  } catch (error) {
    logger.error("Knowledge query failed", { error });
    throw new Error(
      `知识库查询失败: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}

/**
 * 加载法条画像
 */
export async function loadLegalProvisions(
  provisionCodes?: string[],
): Promise<LegalProvision[]> {
  logger.info("Loading legal provisions", { provisionCodes });

  const session = neo4jDriver.session();

  try {
    let query = "MATCH (p:LegalProvision)";
    const params: Record<string, unknown> = {};

    if (provisionCodes && provisionCodes.length > 0) {
      query += " WHERE p.code IN $codes";
      params.codes = provisionCodes;
    }

    query += " RETURN p";

    const result = await session.run(query, params);

    return result.records.map((record) => {
      const p = record.get("p").properties;
      return {
        code: p.code,
        title: p.title,
        content: p.content,
        applicableScenarios: p.applicableScenarios || [],
        relatedCases: p.relatedCases || [],
      };
    });
  } catch (error) {
    logger.error("Failed to load legal provisions", { error });
    throw new Error(
      `法条加载失败: ${error instanceof Error ? error.message : String(error)}`,
    );
  } finally {
    await session.close();
  }
}

/**
 * 查询相关案例
 */
export async function queryRelatedCases(
  keywords: string[],
  limit: number = 10,
): Promise<Array<{ caseId: string; title: string; summary: string }>> {
  logger.info("Querying related cases", { keywords, limit });

  const session = neo4jDriver.session();

  try {
    const query = `
      MATCH (c:Case)-[:HAS_KEYWORD]->(k:Keyword)
      WHERE k.name IN $keywords
      WITH c, COUNT(k) AS relevance
      ORDER BY relevance DESC
      LIMIT $limit
      RETURN c.caseId AS caseId, c.title AS title, c.summary AS summary
    `;

    const result = await session.run(query, { keywords, limit });

    return result.records.map((record) => ({
      caseId: record.get("caseId"),
      title: record.get("title"),
      summary: record.get("summary"),
    }));
  } catch (error) {
    logger.error("Failed to query related cases", { error });
    throw new Error(
      `案例查询失败: ${error instanceof Error ? error.message : String(error)}`,
    );
  } finally {
    await session.close();
  }
}

/**
 * 清理资源
 */
export async function cleanup(): Promise<void> {
  await neo4jDriver.close();
  logger.info("Knowledge service cleaned up");
}

export default {
  vectorSearch,
  queryKnowledge,
  loadLegalProvisions,
  queryRelatedCases,
  cleanup,
};
