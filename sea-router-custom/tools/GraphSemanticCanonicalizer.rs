use std::env;
use std::fs::{self, File};
use std::io::{BufWriter, Write};
use std::path::Path;

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
struct Edge {
    from: u32,
    to: u32,
    weight: u32,
}

fn find_value_start(data: &[u8], key: &str) -> Result<usize, String> {
    let needle = format!("\"{}\"", key);
    let key_pos = data
        .windows(needle.len())
        .position(|window| window == needle.as_bytes())
        .ok_or_else(|| format!("Brak pola '{}'", key))?;
    let mut pos = key_pos + needle.len();
    while pos < data.len() && data[pos].is_ascii_whitespace() {
        pos += 1;
    }
    if data.get(pos) != Some(&b':') {
        return Err(format!("Brak dwukropka po polu '{}'", key));
    }
    pos += 1;
    while pos < data.len() && data[pos].is_ascii_whitespace() {
        pos += 1;
    }
    Ok(pos)
}

fn parse_count(data: &[u8], key: &str) -> Result<u64, String> {
    let mut pos = find_value_start(data, key)?;
    let start = pos;
    while pos < data.len() && data[pos].is_ascii_digit() {
        pos += 1;
    }
    if start == pos {
        return Err(format!("Pole '{}' nie jest liczbą całkowitą", key));
    }
    std::str::from_utf8(&data[start..pos])
        .map_err(|error| error.to_string())?
        .parse::<u64>()
        .map_err(|error| error.to_string())
}

fn visit_array_numbers<F>(data: &[u8], key: &str, mut visitor: F) -> Result<u64, String>
where
    F: FnMut(f64) -> Result<(), String>,
{
    let mut pos = find_value_start(data, key)?;
    if data.get(pos) != Some(&b'[') {
        return Err(format!("Pole '{}' nie jest tablicą", key));
    }
    pos += 1;
    let mut count = 0_u64;
    loop {
        while pos < data.len() && (data[pos].is_ascii_whitespace() || data[pos] == b',') {
            pos += 1;
        }
        if data.get(pos) == Some(&b']') {
            return Ok(count);
        }
        let start = pos;
        while pos < data.len()
            && matches!(data[pos], b'0'..=b'9' | b'-' | b'+' | b'.' | b'e' | b'E')
        {
            pos += 1;
        }
        if start == pos {
            return Err(format!("Nieprawidłowa liczba w tablicy '{}' przy bajcie {}", key, pos));
        }
        let value = std::str::from_utf8(&data[start..pos])
            .map_err(|error| error.to_string())?
            .parse::<f64>()
            .map_err(|error| format!("Nieprawidłowa liczba w '{}': {}", key, error))?;
        if !value.is_finite() {
            return Err(format!("Nieskończona wartość albo NaN w '{}'", key));
        }
        visitor(value)?;
        count += 1;
    }
}

fn exact_u32(value: f64, label: &str) -> Result<u32, String> {
    if value < 0.0 || value > u32::MAX as f64 || value.fract() != 0.0 {
        return Err(format!("{} nie jest dokładną wartością u32: {}", label, value));
    }
    Ok(value as u32)
}

fn canonicalize(input: &Path, nodes_output: &Path, edges_output: &Path) -> Result<(), String> {
    let data = fs::read(input).map_err(|error| error.to_string())?;
    let declared_nodes = parse_count(&data, "nodeCount")?;
    let declared_edges = parse_count(&data, "edgeCount")?;

    let node_file = File::create(nodes_output).map_err(|error| error.to_string())?;
    let mut node_writer = BufWriter::new(node_file);
    node_writer.write_all(b"SRN1").map_err(|error| error.to_string())?;
    node_writer
        .write_all(&declared_nodes.to_le_bytes())
        .map_err(|error| error.to_string())?;
    let node_values = visit_array_numbers(&data, "nodes", |value| {
        let normalized = if value == 0.0 { 0.0 } else { value };
        node_writer
            .write_all(&normalized.to_bits().to_le_bytes())
            .map_err(|error| error.to_string())
    })?;
    node_writer.flush().map_err(|error| error.to_string())?;
    if node_values != declared_nodes * 3 {
        return Err(format!(
            "Niezgodna tablica nodes: {} wartości zamiast {}",
            node_values,
            declared_nodes * 3
        ));
    }

    let capacity = usize::try_from(declared_edges).map_err(|error| error.to_string())?;
    let mut edges = Vec::<Edge>::with_capacity(capacity);
    let mut triple = [0_u32; 3];
    let mut edge_component = 0_u64;
    let edge_values = visit_array_numbers(&data, "edges", |value| {
        let index = (edge_component % 3) as usize;
        triple[index] = exact_u32(value, "Składnik krawędzi")?;
        edge_component += 1;
        if index == 2 {
            edges.push(Edge {
                from: triple[0],
                to: triple[1],
                weight: triple[2],
            });
        }
        Ok(())
    })?;
    if edge_values != declared_edges * 3 || edges.len() as u64 != declared_edges {
        return Err(format!(
            "Niezgodna tablica edges: {} wartości i {} rekordów zamiast {} rekordów",
            edge_values,
            edges.len(),
            declared_edges
        ));
    }
    if edges.iter().any(|edge| edge.from as u64 >= declared_nodes || edge.to as u64 >= declared_nodes) {
        return Err("Krawędź wskazuje nieistniejący identyfikator węzła".to_string());
    }
    edges.sort_unstable();

    let edge_file = File::create(edges_output).map_err(|error| error.to_string())?;
    let mut edge_writer = BufWriter::new(edge_file);
    edge_writer.write_all(b"SRE1").map_err(|error| error.to_string())?;
    edge_writer
        .write_all(&declared_edges.to_le_bytes())
        .map_err(|error| error.to_string())?;
    for edge in edges {
        edge_writer
            .write_all(&edge.from.to_le_bytes())
            .and_then(|_| edge_writer.write_all(&edge.to.to_le_bytes()))
            .and_then(|_| edge_writer.write_all(&edge.weight.to_le_bytes()))
            .map_err(|error| error.to_string())?;
    }
    edge_writer.flush().map_err(|error| error.to_string())?;
    println!("node_count={}", declared_nodes);
    println!("edge_count={}", declared_edges);
    Ok(())
}

fn main() {
    let arguments: Vec<String> = env::args().collect();
    if arguments.len() != 4 {
        eprintln!("Użycie: GraphSemanticCanonicalizer <graf.json> <nodes.bin> <edges.bin>");
        std::process::exit(2);
    }
    if let Err(error) = canonicalize(
        Path::new(&arguments[1]),
        Path::new(&arguments[2]),
        Path::new(&arguments[3]),
    ) {
        eprintln!("Błąd: {}", error);
        std::process::exit(1);
    }
}
