import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const articlesCollection = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/articles' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    publishedDate: z.string(),
    modifiedDate: z.string().optional(),
    author: z.string().default('DataMgmt Team'),
    heroImage: z.string().optional(),
    tags: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
    // SEO fields
    keywords: z.array(z.string()).optional(),
    canonical: z.string().optional(),
  }),
});

const comparisonsCollection = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/comparisons' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    competitor: z.string(),
    competitorType: z.enum(['centralized', 'decentralized', 'hybrid']),
    lastUpdated: z.string().optional(),
  }),
});

export const collections = {
  articles: articlesCollection,
  comparisons: comparisonsCollection,
};
