import os, sys

import pandas as pd
import numpy as np
import networkx as nx
from pyvis.network import Network
import igraph as ig
import matplotlib.pyplot as plt


def page_info(pages):

    ndomains = len(np.unique(list(pages["domain"])))
    npages = len(np.unique(list(pages["url"])))
    ndups = len(np.unique(list(pages[pages["page_type_code"] == "DUPLICATE"]["url"])))

    return {
        "domains": {"n": ndomains, "per dom": None, "per page": None},
        "pages": {"n": npages, "per dom": npages/ndomains, "per page": None},
        "duplicates": {"n": ndups, "per dom": ndups/ndomains, "per page": ndups/npages}
    }

def data_info(data):
    pdf = len([tp for tp in list(data["data_type_code"]) if (isinstance(tp, str) and ("PDF" in tp))])
    doc = len([tp for tp in list(data["data_type_code"]) if (isinstance(tp, str) and ("DOC" in tp or "DOCX" in tp))])
    ppt = len([tp for tp in list(data["data_type_code"]) if (isinstance(tp, str) and ("PPT" in tp or "PPTX" in tp))])

    return pdf, doc, ppt

def image_info(images):
    return (len(list(images["id"])))


def get_table(pages, data, images):
    stats_all = page_info(pages)
    ndoms, npages = stats_all["domains"]["n"], stats_all["pages"]["n"]
    npdf, ndoc, nppt = data_info(data)
    stats_all["PDF"] = {"n": npdf, "per dom": npdf/ndoms, "per page": npdf/npages}
    stats_all["DOC"] = {"n": ndoc, "per dom": ndoc/ndoms, "per page": ndoc/npages}
    stats_all["PPT"] = {"n": nppt, "per dom": nppt/ndoms, "per page": nppt/npages}
    nimg = image_info(images)
    stats_all["Images"] = {"n": nimg, "per dom": nimg/ndoms, "per page": nimg/npages}
    
    

    table = pd.DataFrame.from_dict(stats_all, orient="index")
    return table


def viz_network(node_types, edges):
    pass


if __name__ == "__main__":
    
    pages = pd.read_csv("pages.csv")
    data = pd.read_csv("data.csv") #, index_col="id")
    images = pd.read_csv("images.csv")
    links = pd.read_csv("links.csv") 

    table_all = get_table(pages, data, images)
    print(table_all)

    seeds = ["gov.si", "evem.gov.si", "e-uprava.gov.si", "e-prostor.gov.si"]
    s_pages = pages[(pages["domain"].isin(seeds))]
    s_ids = list(s_pages["id"])
    #[print(p[1]["id"], p[1]["url"]) for p in s_pages.iterrows()]
    #print(s_ids)
    s_data = data[(data["page_id"].isin(s_ids))]
    s_images = images[(images["page_id"].isin(s_ids))]
    table_seeds = get_table(s_pages, s_data, s_images)
    print(table_seeds)


    #site_dict = {l[0]: l[2] for i, l in links.iterrows()}
    #for key in site_dict:
    #    if site_dict[key] > 4: site_dict[key] = 0
    #print(site_dict)

    nodes_from = np.unique(list(links["from_page"]))
    #nodes_to = np.unique(list(links["to_page"]))
    #nodes = np.unique(np.concatenate([nodes_from, nodes_to])).astype(int)
    nodes = nodes_from
    print(len(nodes))
    links = links[links["to_page"].isin(nodes)]
    edges = list(zip(list(links["from_page"]), list(links["to_page"])))


    dmap = dict(zip(links['from_page'], links['site_id']))
    to_site = []
    for to_page in list(links["to_page"]):
        if to_page in dmap:
            to_site.append(dmap[to_page])
        else:
            to_site.append(None)

    to_site = np.array(to_site)
    from_site = np.array(links["site_id"])[to_site != None]
    to_site = to_site[to_site != None]
    notequal = (to_site != from_site)
    from_site = from_site[notequal]
    to_site = to_site[notequal]
    print(len(from_site), len(to_site))
    print(from_site[:10])
    print(to_site[:10])

    G = nx.Graph()
    G.add_edges_from(zip(from_site, to_site))
    print(G)
    print(len(G.nodes))

    nx.draw_kamada_kawai(G)
    plt.show()


    # G = nx.Graph()
    # G.add_nodes_from(nodes)
    # G.add_edges_from(edges)
    # nx.draw(G)
    # plt.show()

    # visnet = Network(notebook=True)
    # visnet.from_nx(G)
    # visnet.show("links.html")

    # g = ig.Graph(edges=edges)
    # layout = g.layout(layout='auto')
    # ig.plot(g)