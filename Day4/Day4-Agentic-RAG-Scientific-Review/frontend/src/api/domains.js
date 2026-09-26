import client from "./client";

export async function fetchDomains() {
  const { data } = await client.get("/domains");
  return data;
}
