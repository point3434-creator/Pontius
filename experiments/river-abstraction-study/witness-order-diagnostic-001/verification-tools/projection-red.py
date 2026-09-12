"""Inference-only projection of witness-major threshold probabilities."""
def triplet(values):
    return list(values)

def project(rows):
    return [sum((triplet(row[i:i+3]) for i in (0,3,6)),[]) for row in rows]
