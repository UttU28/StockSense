import { z } from "zod";

export const insertItemSchema = z.object({
  title: z.string().min(1, "Title is required"),
  description: z.string().min(1, "Description is required"),
  category: z.string().min(1, "Category is required"),
});

export type InsertItem = z.infer<typeof insertItemSchema>;

export type Item = {
  id: number;
  title: string;
  description: string;
  category: string;
};

