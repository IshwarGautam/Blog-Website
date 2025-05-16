const { Pool } = require("pg");

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

exports.handler = async function (event) {
  if (event.httpMethod !== "POST") {
    return {
      statusCode: 405,
      body: "Method Not Allowed",
    };
  }

  try {
    const data = JSON.parse(event.body);
    const { slug, name, content, parent_id } = data;

    if (!slug || !name || !content) {
      return {
        statusCode: 400,
        body: "Missing required fields",
      };
    }

    // Get post_id from slug
    const postRes = await pool.query("SELECT id FROM posts WHERE slug = $1", [slug]);

    if (postRes.rows.length === 0) {
      return {
        statusCode: 404,
        body: "Post not found"
      };
    }

    const postId = postRes.rows[0].id;

    // Insert comment
    await pool.query(
      "INSERT INTO comment (post_id, name, content, parent_id, timestamp) VALUES ($1, $2, $3, $4, NOW())",
      [postId, name, content, parent_id || null]
    );

    return {
      statusCode: 200,
      body: "Comment submitted successfully",
    };
  } catch (error) {
    console.error("Error submitting comment:", error);
    return {
      statusCode: 500,
      body: "Internal Server Error",
    };
  }
};
