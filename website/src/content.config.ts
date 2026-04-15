import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const docsCollection = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/docs' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    order: z.number().default(0),
    category: z.enum(['getting-started', 'user-guide', 'development', 'operations']).optional(),
    tags: z.array(z.string()).default([]),
    lastUpdated: z.string().optional(),
  }),
});

const blogCollection = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/blog' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    publishedDate: z.string(),
    modifiedDate: z.string().optional(),
    author: z.string().default('DataMgmt Team'),
    heroImage: z.string().optional(),
    tags: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
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
  docs: docsCollection,
  blog: blogCollection,
  comparisons: comparisonsCollection,
};
