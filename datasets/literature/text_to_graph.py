import matplotlib.pyplot as plt
import networkx as nx
from langchain.chains import GraphQAChain
from langchain_community.graphs.networkx_graph import NetworkxEntityGraph
from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_openai import ChatOpenAI


def create_graph_from_documents(documents, llm):
    llm_transformer_filtered = LLMGraphTransformer(
        llm=llm,
        allowed_nodes=["Person", "Country", "Organization"],
        allowed_relationships=[
            "NATIONALITY",
            "LOCATED_IN",
            "WORKED_AT",
            "SPOUSE",
            "CHILD",
        ],
    )
    graph_documents_filtered = llm_transformer_filtered.convert_to_graph_documents(
        documents
    )

    graph = NetworkxEntityGraph()

    # Add nodes to the graph
    for node in graph_documents_filtered[0].nodes:
        graph.add_node(node.id)

    # Add edges to the graph
    for edge in graph_documents_filtered[0].relationships:
        graph._graph.add_edge(
            edge.source.id,
            edge.target.id,
            relation=edge.type,
        )

    return graph


def visualize_graph(graph, output_file="graph.png"):
    plt.figure(figsize=(12, 12))
    pos = nx.spring_layout(graph._graph, k=0.1, iterations=50)
    nx.draw(
        graph._graph,
        pos,
        with_labels=True,
        node_size=2800,
        node_color="lightblue",
        font_size=10,
        font_weight="bold",
    )
    edge_labels = nx.get_edge_attributes(graph._graph, "relation")
    nx.draw_networkx_edge_labels(
        graph._graph, pos, edge_labels=edge_labels, font_size=8
    )
    plt.title("Graph Visualization")
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()


def main():
    text = """
    Marie Curie, born in 1867, was a Polish and naturalised-French physicist and chemist who conducted pioneering research on radioactivity.
    She was the first woman to win a Nobel Prize, the first person to win a Nobel Prize twice, and the only person to win a Nobel Prize in two scientific fields.
    Her husband, Pierre Curie, was a co-winner of her first Nobel Prize, making them the first-ever married couple to win the Nobel Prize and launching the Curie family legacy of five Nobel Prizes.
    She was, in 1906, the first woman to become a professor at the University of Paris.
    Marie Curie's daughters were Irène Joliot-Curie and Ève Curie. Irène was married to Frédéric Joliot-Curie, and Ève was married to Henry Labouisse.
    """

    llm = ChatOpenAI(model="gpt-4o-mini")
    documents = [Document(page_content=text)]
    graph = create_graph_from_documents(documents, llm)
    visualize_graph(graph)

    chain = GraphQAChain.from_llm(llm=llm, graph=graph, verbose=True)
    question = """Who is Marie Curie?"""
    answer = chain.invoke(question)
    print(answer)


if __name__ == "__main__":
    main()
