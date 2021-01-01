main = []
beta_versions = {
    1.0: [0.95 + 0.001 * i for i in range(2, 5)]
}

beta = []

for i in beta_versions.keys(): beta.extend(beta_versions[i])

supporting = [*main, *beta]
supporting.sort()

current = supporting[-1]